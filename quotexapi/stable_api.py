
import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests
import websocket

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


class Quotex:
    """
    A class for interacting with the Quotex API.
    """
    URL = 'https://qx-platform.webull.io'
    API_URL = 'wss://qx-platform.webull.io/socket.io/?EIO=4&transport=websocket'

    def __init__(self, email: str, password: str, proxies: Optional[Dict[str, str]] = None,
                 server_url: str = API_URL):
        """
        Initializes a Quotex instance.

        :param email: The user's email.
        :param password: The user's password.
        :param proxies: Optional dictionary of proxies.
        """
        self.email = email
        self.password = password
        self.server_url = server_url
        self.session = requests.Session()
        self.session.proxies = proxies
        self.websocket_client = None
        self.is_connected = False
        self.request_id = 0
        self.lock = asyncio.Lock()
        self.signals_trade: Dict[int, Dict[str, Any]] = {}
        self.request_data: Dict[int, Any] = {}
        self.request_data_lock = threading.Lock()
        self.account_balance = 0
        self.token: Optional[str] = None
        self.ssid: Optional[str] = None
        self.message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.subscribed_assets: List[str] = []

    def _get_ssid(self) -> Optional[str]:
        """
        Retrieves the session ID (ssid).

        :return: The session ID (ssid) or None if an error occurs.
        """
        try:
            url = f"{self.URL}/s/login"
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'
            }
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                ssid = response.cookies.get("ssid")
                return ssid
            return None
        except requests.RequestException as e:
            logging.error(f"Error getting ssid: {e}")
            return None

    def _login(self, ssid: str) -> Optional[str]:
        """
        Logs in to the Quotex platform.

        :param ssid: The session ID (ssid).
        :return: The authentication token or None if an error occurs.
        """
        try:
            url = f"{self.URL}/api/v2/login"
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'cookie': f'ssid={ssid}',
                'origin': self.URL,
                'referer': f'{self.URL}/',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'
            }
            payload = {"email": self.email, "password": self.password}
            response = self.session.post(
                url, headers=headers, data=json.dumps(payload))
            response_json = response.json()
            if response.status_code == 200 and response_json.get("status") == "success":
                token = response_json.get("token")
                return token
            return None
        except requests.RequestException as e:
            logging.error(f"Error logging in: {e}")
            return None

    async def connect(self) -> Tuple[bool, Optional[str]]:
        """
        Connects to the Quotex WebSocket.

        :return: A tuple containing a boolean indicating success and an optional error message.
        """
        self.ssid = self._get_ssid()
        if not self.ssid:
            return False, "Failed to get ssid"

        self.token = self._login(self.ssid)
        if not self.token:
            return False, "Failed to login"

        self.websocket_client = websocket.WebSocketApp(
            f"{self.server_url}&token={self.token}",
            on_message=self._on_message,
            on_open=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            cookie=f"ssid={self.ssid}"
        )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.websocket_client.run_forever)
        return self.is_connected, None

    def _on_open(self, ws: websocket.WebSocketApp):
        """
        Handles the WebSocket open event.
        """
        logging.info("WebSocket connection opened.")
        self.is_connected = True
        self.send_heartbeat_thread = threading.Thread(
            target=self._send_heartbeat, daemon=True)
        self.send_heartbeat_thread.start()

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str):
        """
        Handles the WebSocket close event.
        """
        logging.info(
            f"WebSocket connection closed with code {close_status_code}: {close_msg}")
        self.is_connected = False

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception):
        """
        Handles WebSocket errors.
        """
        logging.error(f"WebSocket error: {error}")
        self.is_connected = False

    def _on_message(self, ws: websocket.WebSocketApp, message: str):
        """
        Handles incoming WebSocket messages.
        """
        if message == "2":
            self.send_message("3")
            return
        if message.startswith("42"):
            try:
                data = json.loads(message[2:])
                event_name = data[0]
                event_data = data[1]
                if "balance" in event_data:
                    self.account_balance = event_data["balance"]

                with self.request_data_lock:
                    if event_name in self.request_data:
                        self.request_data[event_name].append(event_data)

            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON: {message}")
        if self.message_callback:
            self.message_callback(json.loads(message[2:]))

    def _send_heartbeat(self):
        """
        Sends heartbeat messages to keep the connection alive.
        """
        while self.is_connected:
            try:
                self.send_message("2")
                time.sleep(20)
            except websocket.WebSocketConnectionClosedException:
                break

    def send_message(self, message: str, params: Optional[Any] = None) -> int:
        """
        Sends a message through the WebSocket.

        :param message: The message to send.
        :param params: Optional parameters for the message.
        :return: The request ID.
        """
        with self.request_data_lock:
            self.request_id += 1
            if params:
                self.websocket_client.send(
                    f'42{json.dumps([message, params])}')
            else:
                self.websocket_client.send(f'42{json.dumps([message])}')
            return self.request_id

    async def get_payment_methods(self):
        """
        Get list of payment methods
        """
        self.send_message('get-payment-methods')
        return self._wait_for_response('get-payment-methods')

    async def get_history_trades(self):
        """
        Get history trades from account
        """
        self.send_message('get-history-trades')
        return self._wait_for_response('get-history-trades')

    async def _wait_for_response(self, event_name: str, timeout: int = 10) -> Any:
        """
        Waits for a response for a specific event.

        :param event_name: The event name to wait for.
        :param timeout: The timeout in seconds.
        :return: The event data or None if a timeout occurs.
        """
        with self.request_data_lock:
            self.request_data[event_name] = []
        for _ in range(timeout):
            await asyncio.sleep(1)
            with self.request_data_lock:
                if self.request_data.get(event_name):
                    data = self.request_data.pop(event_name)
                    return data
        return None

    def check_connect(self) -> bool:
        """
        Checks if the WebSocket is connected.

        :return: True if connected, False otherwise.
        """
        return self.is_connected

    async def close(self):
        """
        Closes the WebSocket connection.
        """
        if self.is_connected:
            self.websocket_client.close()

    async def trade(self, amount: int, asset: str, direction: str, duration: int) -> Optional[int]:
        """
        Places a trade.

        :param amount: The amount to trade.
        :param asset: The asset to trade.
        :param direction: The trade direction ('call' or 'put').
        :param duration: The trade duration in seconds.
        :return: The trade ID or None if an error occurs.
        """
        if direction not in ['call', 'put']:
            logging.error("Invalid direction. Must be 'call' or 'put'.")
            return None
        if asset not in self.subscribed_assets:
            self.subscribe_asset(asset)
            await asyncio.sleep(1)
        params = {
            "amount": amount,
            "asset": asset,
            "direction": direction,
            "duration": duration,
        }
        self.send_message('new-option', params)
        data = await self._wait_for_response('new-option')
        return data

    async def check_win(self, asset: str, trade_id: int):
        """
        Check if a trade was a win.

        :param asset: The asset of the trade.
        :param trade_id: The ID of the trade.
        :return: The result of the trade or None.
        """
        self.send_message("get-option-rate",
                          {"asset": asset, "id": trade_id})
        data = await self._wait_for_response('option-rate-changed')
        return data

    async def get_candles(self, asset: str, interval: int, count: int, end_time: int):
        """
        Retrieves candle data for an asset.

        :param asset: The asset to retrieve candles for.
        :param interval: The candle interval in seconds.
        :param count: The number of candles to retrieve.
        :param end_time: The end time of the candles.
        :return: The candle data.
        """
        params = {"asset": asset, "interval": interval,
                  "count": count, "to": end_time}
        self.send_message("get-candles", params)
        data = await self._wait_for_response("candles")
        return data

    async def get_balance(self) -> float:
        """
        Retrieves the account balance.

        :return: The account balance.
        """
        self.send_message('get-balance')
        await self._wait_for_response('balance-changed')
        return self.account_balance

    def subscribe_asset(self, assets: Union[str, List[str]]):
        """
        Subscribes to real-time asset data.

        :param assets: A single asset or a list of assets to subscribe to.
        """

        assets_to_subscribe = [assets] if isinstance(
            assets, str) else assets

        for asset in assets_to_subscribe:
            if asset not in self.subscribed_assets:
                self.send_message("subscribe", asset)
                self.subscribed_assets.append(asset)

    def unsubscribe_asset(self, assets: Union[str, List[str]]):
        """
        Unsubscribes from real-time asset data.

        :param assets: A single asset or a list of assets to unsubscribe from.
        """
        assets_to_unsubscribe = [assets] if isinstance(
            assets, str) else assets
        for asset in assets_to_unsubscribe:
            if asset in self.subscribed_assets:
                self.send_message("unsubscribe", asset)
                self.subscribed_assets.remove(asset)

    @staticmethod
    def get_assets():
        """
        Retrieves a list of available assets.

        :return: A dictionary of available assets.
        """
        try:
            url = f"{Quotex.URL}/api/v1/pairs"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            logging.error(f"Error getting assets: {e}")
            return None

    @staticmethod
    def get_signal_all() -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves all trading signals.

        :return: A list of trading signals or None if an error occurs.
        """
        try:
            url = f"{Quotex.URL}/api/v1/signals"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            logging.error(f"Error getting signals: {e}")
            return None


if __name__ == '__main__':
    async def main():
        """
        Example usage of the Quotex class.
        """
        email = "email"
        password = "password"
        quotex = Quotex(email, password)
        try:
            check, reason = await quotex.connect()
            if check:
                logging.info("Successfully connected.")
                all_assets = quotex.get_assets()
                # print all assets from all_assets['pairs']
                for asset in all_assets['pairs']:
                    print(asset)
                # Subscribe to an asset
                quotex.subscribe_asset("EURUSD")
                await asyncio.sleep(5)  # Wait for data
                # Place a trade
                trade_id = await quotex.trade(1, "EURUSD", "call", 60)
                if trade_id:
                    logging.info(f"Trade placed with ID: {trade_id}")
                    await asyncio.sleep(60)  # Wait for the trade to expire
                    # Check the result
                    result = await quotex.check_win("EURUSD", trade_id)
                    logging.info(f"Trade result: {result}")
                # Unsubscribe
                quotex.unsubscribe_asset("EURUSD")
                # Get candles
                candles = await quotex.get_candles("EURUSD", 60, 100, int(time.time()))
                logging.info(f"Candles: {candles}")
                # Get balance
                balance = await quotex.get_balance()
                logging.info(f"Balance: {balance}")

            else:
                logging.error(f"Connection failed: {reason}")
        finally:
            await quotex.close()

    asyncio.run(main())

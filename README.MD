# Quotex Real-Time Signal Generator for Firebase

This project is a real-time trading signal generator for the Quotex platform. It connects to Quotex, fetches live data for all available crypto assets, calculates technical indicators, generates trading signals, and pushes them to a Firebase Firestore database in real-time. This allows you to power a live dashboard or any other application with these signals.

## How It Works

1.  **Authentication**: The script logs into your Quotex account using the email and password provided as environment variables.
2.  **Asset Discovery**: It fetches the list of all currently tradable crypto assets.
3.  **Real-Time Data Fetching**: For each asset, it continuously fetches live 1-minute candlestick data.
4.  **Signal Generation**: On receiving new data, it calculates the following technical indicators:
    *   Relative Strength Index (RSI)
    *   Bollinger Bands (BB)
    *   Exponential Moving Average (EMA)

    Based on the values of these indicators, it generates a trading signal: `BUY`, `SELL`, or `NEUTRAL`.
5.  **Firestore Integration**: The generated signals and indicator data for all assets are updated in a Firebase Firestore database in real-time. Your web dashboard or application can then read from this database to display the signals.

## Deployment on Vercel

This project is designed to be deployed as a serverless function on Vercel.

### Prerequisites

*   A Vercel account.
*   A Firebase project with Firestore enabled.
*   Your Quotex account credentials (email and password).

### Setup and Deployment

1.  **Fork this Repository**: Start by forking this repository to your own GitHub account.

2.  **Connect to Vercel**: In your Vercel dashboard, create a new project and connect it to your forked GitHub repository.

3.  **Configure Environment Variables**: This is the most crucial step. In your Vercel project settings, go to **Settings > Environment Variables** and add the following:

    *   `QUOTEX_EMAIL`: Your Quotex account email.
    *   `QUOTEX_PASSWORD`: Your Quotex account password.
    *   `FIREBASE_CONFIG_JSON`: This is the JSON configuration for your Firebase project. 
        *   Go to your Firebase project settings.
        *   Under **Service accounts**, generate a new private key.
        *   This will download a JSON file. **Copy the entire content of that JSON file** and paste it as the value for this environment variable.

4.  **Deploy**: After setting the environment variables, trigger a new deployment in Vercel. Vercel will automatically install the dependencies and deploy the function.

## Project Structure

```
/
|-- functions/
|   |-- git-quotex-api-v2/
|       |-- improved_signal_generator_all_assets_adapted.py  (The main signal generation logic)
|       |-- requirements.txt                                 (Python dependencies)
|-- .gitignore                                             (To prevent secrets from being committed)
|-- vercel.json                                            (Vercel configuration)
|-- README.MD                                              (This file)
```

## Important Notes

*   **Security**: Your `FIREBASE_CONFIG_JSON` contains sensitive credentials. It is stored securely as an environment variable in Vercel and is not exposed in the code, thanks to the `.gitignore` file.
*   **Real-time Updates**: The script runs continuously to provide real-time signals. Ensure your Vercel plan supports this kind of execution if you need it to run 24/7.
*   **Quotex API**: This script relies on an unofficial Quotex API. Changes in the Quotex platform may break the script. Regular maintenance might be required.

'use client';

import { useEffect, useState, useRef } from 'react';

const pollIntervalMs = 5000;
const alertTone = 'data:audio/wav;base64,UklGRjQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAADQAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';

export default function Home() {
  const [signal, setSignal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  const fetchSignal = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/signal');
      if (!res.ok) {
        throw new Error(`status ${res.status}`);
      }
      const data = await res.json();
      setSignal(data.active_signal || data);

      const conf = data.active_signal?.confidence ?? 0;
      if (conf >= 90 && audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(() => {});
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignal();
    const interval = setInterval(fetchSignal, pollIntervalMs);
    return () => clearInterval(interval);
  }, []);

  const isScanning = !signal || signal.signal === 'SCANNING';
  const statusText = isScanning ? 'SCANNING...' : signal.direction ? `${signal.direction} ${signal.asset || ''}` : 'NO SIGNAL';
  const confidence = signal?.confidence ?? 0;

  return (
    <main className="page-shell">
      <audio ref={audioRef} src={alertTone} preload="auto" />
      <div className="terminal-card">
        <div className="heading">Trading Signal Terminal</div>
        <div className={`status-badge ${isScanning ? 'scanning' : signal.direction === 'BUY' ? 'buy' : 'sell'}`}>
          {statusText}
        </div>
        <div className="metrics">
          <div className="metric">
            <span>Confidence</span>
            <strong>{isScanning ? '--' : `${confidence}%`}</strong>
          </div>
          <div className="metric">
            <span>Price</span>
            <strong>{isScanning ? '--' : `$${signal.price ?? '---'}`}</strong>
          </div>
          <div className="metric">
            <span>RSI</span>
            <strong>{isScanning ? '--' : signal.rsi ?? '--'}</strong>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="hint">Auto refresh every 5 sec · last update: {new Date().toLocaleTimeString()}</div>
      </div>
      <div className="futuristic-grid">
        {signal && !isScanning && (
          <pre>{JSON.stringify(signal, null, 2)}</pre>
        )}
      </div>
    </main>
  );
}

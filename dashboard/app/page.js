'use client';

import { useEffect, useState, useRef } from 'react';

const pollIntervalMs = 5000;
const alertTone = 'data:audio/wav;base64,UklGRjQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAADQAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';

export default function Home() {
  const [activeSignal, setActiveSignal] = useState(null);
  const [allSignals, setAllSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('SCANNING');
  const audioRef = useRef(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchSignal = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/signal');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();

      if (data.all_signals && data.all_signals.length > 0) {
        setAllSignals(data.all_signals);
        setActiveSignal(data.active_signal || data.all_signals[0]);
        setStatus('ACTIVE');
        if ((data.active_signal?.confidence ?? 0) >= 90 && audioRef.current) {
          audioRef.current.currentTime = 0;
          audioRef.current.play().catch(() => {});
        }
      } else if (data.signal === 'SCANNING') {
        setStatus('SCANNING');
        setActiveSignal(null);
        setAllSignals([]);
      } else {
        setStatus(data.status || 'READY');
      }

      if (data.error) {
        setError(data.error);
      }
    } catch (e) {
      setError(`Fetch error: ${e.message}`);
      setStatus('ERROR');
    } finally {
      setLoading(false);
      setLastUpdate(new Date());
    }
  };

  useEffect(() => {
    fetchSignal();
    const interval = setInterval(fetchSignal, pollIntervalMs);
    return () => clearInterval(interval);
  }, []);

  const isScanning = status === 'SCANNING';
  const hasSignal = activeSignal && activeSignal.direction;
  const signalColor = hasSignal ? (activeSignal.direction === 'BUY' ? '#10b981' : '#ef4444') : '#64748b';
  const signalBgColor = hasSignal
    ? (activeSignal.direction === 'BUY' ? 'rgb(16, 185, 129, 0.1)' : 'rgb(239, 68, 68, 0.1)')
    : 'rgb(100, 116, 139, 0.1)';

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6">
      <audio ref={audioRef} src={alertTone} preload="auto" />

      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-emerald-400 mb-2">⚡ Trading Signal Terminal</h1>
          <p className="text-slate-400">Real-time market analysis powered by AI</p>
        </div>

        <div
          className="mb-8 rounded-2xl border-2 p-8 transition-all duration-300"
          style={{
            borderColor: signalColor,
            backgroundColor: signalBgColor,
            boxShadow: `0 0 30px ${signalColor}40`,
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
                {isScanning ? '🔄 Scanning Market' : '✅ Active Signal'}
              </div>
              <div className="text-6xl font-black mb-6" style={{ color: signalColor }}>
                {isScanning ? 'SCANNING...' : hasSignal ? `${activeSignal.direction}` : 'WAITING'}
              </div>
              {hasSignal && (
                <>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-xl font-bold text-white">{activeSignal.asset}</span>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-semibold"
                      style={{
                        backgroundColor: signalColor,
                        color: activeSignal.direction === 'BUY' ? '#050505' : '#fff',
                      }}
                    >
                      ${activeSignal.price}
                    </span>
                  </div>
                  <div className="text-slate-300 text-sm">
                    <p>🎯 Confidence: <strong>{activeSignal.confidence}%</strong></p>
                    <p>📊 RSI: <strong>{activeSignal.rsi}</strong></p>
                    <p>⏰ {new Date(activeSignal.timestamp).toLocaleTimeString()}</p>
                  </div>
                </>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 uppercase mb-2">RSI(14)</div>
                <div className="text-3xl font-bold text-blue-400">{hasSignal ? activeSignal.rsi : '--'}</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 uppercase mb-2">EMA5/20</div>
                <div className="text-lg font-bold text-purple-400">
                  {hasSignal ? activeSignal.ema5.toFixed(3) : '--'} / {hasSignal ? activeSignal.ema20.toFixed(3) : '--'}
                </div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 uppercase mb-2">Upper BB</div>
                <div className="text-2xl font-bold text-orange-400">{hasSignal ? activeSignal.upper_bb : '--'}</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 uppercase mb-2">Lower BB</div>
                <div className="text-2xl font-bold text-cyan-400">{hasSignal ? activeSignal.lower_bb : '--'}</div>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-6 bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-300 text-sm">
              <strong>⚠️ Error:</strong> {error}
            </div>
          )}
        </div>

        {allSignals.length > 0 && (
          <div className="rounded-2xl border border-slate-700 overflow-hidden">
            <div className="bg-slate-800 px-6 py-4 border-b border-slate-700">
              <h2 className="text-lg font-bold text-emerald-400">📊 All Signals ({allSignals.length})</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-800/50 border-b border-slate-700">
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">Asset</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">Signal</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">Confidence</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">Price</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">RSI</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">EMA5/20</th>
                    <th className="px-6 py-3 text-left text-slate-300 font-semibold">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {allSignals.map((sig, idx) => (
                    <tr key={idx} className="border-b border-slate-700 hover:bg-slate-800/50 transition">
                      <td className="px-6 py-4 font-bold text-white">{sig.asset}</td>
                      <td className="px-6 py-4">
                        <span
                          className="px-3 py-1 rounded font-bold"
                          style={{
                            backgroundColor: sig.direction === 'BUY' ? 'rgb(16, 185, 129, 0.2)' : 'rgb(239, 68, 68, 0.2)',
                            color: sig.direction === 'BUY' ? '#10b981' : '#ef4444',
                          }}
                        >
                          {sig.direction}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-yellow-400 font-bold">{sig.confidence}%</span>
                      </td>
                      <td className="px-6 py-4 text-white">${sig.price.toFixed(5)}</td>
                      <td className="px-6 py-4 text-blue-400">{sig.rsi.toFixed(1)}</td>
                      <td className="px-6 py-4 text-purple-400">
                        {sig.ema5.toFixed(3)} / {sig.ema20.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 text-slate-400">{new Date(sig.timestamp).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-8 flex items-center justify-between bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isScanning ? 'animate-pulse' : ''}`} style={{ backgroundColor: signalColor }} />
            <span className="text-slate-300">
              {isScanning ? 'Scanning...' : hasSignal ? 'Signal Active' : 'Waiting for signals'} •{' '}
              <span className="text-slate-400 text-xs">Updated: {lastUpdate.toLocaleTimeString()}</span>
            </span>
          </div>
          <button
            onClick={fetchSignal}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .animate-pulse {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>
    </main>
  );
}

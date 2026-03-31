
import { useEffect, useRef } from 'react';

const ActiveSignal = ({ signal }) => {
  const audioRef = useRef(null);

  // এই useEffect হুকটি সিগন্যাল পরিবর্তন হলে অডিও বাজানোর জন্য কাজ করবে
  useEffect(() => {
    if (signal && signal.confidence > 85) {
      if (audioRef.current) {
        audioRef.current.play().catch(error => console.log("Audio playback was prevented by the browser."));
      }
    }
  }, [signal]); // সিগন্যাল পরিবর্তন হলে এই হুকটি আবার চলবে

  if (!signal) {
    return null;
  }

  // সিগন্যালের উপর ভিত্তি করে CSS ক্লাস পরিবর্তন
  const signalClass = signal.signal === 'Buy' ? 'text-green-400' : 'text-red-400';
  const confidenceColor = signal.confidence > 85 ? 'text-yellow-300' : 'text-blue-300';

  return (
    <div className="w-full max-w-md p-8 bg-gray-800 rounded-xl shadow-lg text-center">
      <h2 className="text-2xl font-bold mb-4 text-gray-300">Live Signal</h2>
      
      <div className="mb-6">
        <p className="text-lg text-gray-400">Asset</p>
        <p className="text-5xl font-extrabold text-white tracking-widest">{signal.asset.replace('_otc', '').toUpperCase()}</p>
      </div>
      
      <div className="mb-6">
        <p className="text-lg text-gray-400">Direction</p>
        <p className={`text-6xl font-extrabold ${signalClass}`}>{signal.signal.toUpperCase()}</p>
      </div>

      <div className="mb-2">
        <p className="text-lg text-gray-400">Confidence Level</p>
        <p className={`text-4xl font-bold ${confidenceColor}`}>{signal.confidence}%</p>
      </div>

      {/* অডিও ফাইল (এটি লুকানো থাকবে) */}
      <audio ref={audioRef} src="/alert.mp3" preload="auto"></audio>
    </div>
  );
};

export default ActiveSignal;

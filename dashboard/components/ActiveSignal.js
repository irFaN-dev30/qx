
import { useEffect, useState } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';

const ActiveSignal = ({ db }) => {
  const [signal, setSignal] = useState(null);
  const [audio, setAudio] = useState(null);

  useEffect(() => {
    const audio = new Audio('/alert.mp3');
    setAudio(audio);

    const unsub = onSnapshot(doc(db, 'signals', 'active'), (doc) => {
      const newSignal = doc.data();
      setSignal(newSignal);
      if (newSignal?.confidence > 0.8) { // Assuming 'Strong' signal is > 80% confidence
        audio.play();
      }
    });
    return () => unsub();
  }, [db]);

  return (
    <div className="bg-gray-900 border-2 border-emerald-neon rounded-lg p-8 w-full max-w-md text-center">
      <h2 className="text-2xl font-bold mb-4">Active Signal</h2>
      {signal ? (
        <>
          <p className="text-lg">{signal.asset}</p>
          <p className={`text-4xl font-bold ${signal.signal === 'Buy' ? 'text-emerald-neon' : 'text-crimson-red'}`}>
            {signal.signal}
          </p>
          <p className="text-lg">Confidence: {signal.confidence * 100}%</p>
          <p className="text-sm">Candle ends in: {signal.countdown}s</p>
        </>
      ) : (
        <p>No active signal...</p>
      )}
    </div>
  );
};

export default ActiveSignal;

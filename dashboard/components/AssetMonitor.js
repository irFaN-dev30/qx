
import { useEffect, useState } from 'react';
import { collection, onSnapshot } from 'firebase/firestore';

const AssetMonitor = ({ db }) => {
  const [signals, setSignals] = useState([]);

  useEffect(() => {
    const unsub = onSnapshot(collection(db, 'all_signals'), (snapshot) => {
      const newSignals = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
      setSignals(newSignals);
    });
    return () => unsub();
  }, [db]);

  return (
    <div className="w-64 bg-gray-900 p-4 overflow-y-auto">
      <h2 className="text-xl font-bold mb-4">Asset Monitor</h2>
      <ul>
        {signals.map((signal) => (
          <li key={signal.id} className="flex justify-between items-center mb-2">
            <span>{signal.id}</span>
            <span className={signal.signal === 'Buy' ? 'text-emerald-neon' : 'text-crimson-red'}>
              {signal.signal}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AssetMonitor;


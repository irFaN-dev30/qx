
import Head from 'next/head';
import AssetMonitor from '../components/AssetMonitor';
import ActiveSignal from '../components/ActiveSignal';

export default function Home({ db }) {
  return (
    <div>
      <Head>
        <title>Real-Time Trading Signal Dashboard</title>
        <meta name="description" content="Real-Time Trading Signal Dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex h-screen">
        <AssetMonitor db={db} />
        <div className="flex-1 flex items-center justify-center">
          <ActiveSignal db={db} />
        </div>
      </main>
    </div>
  );
}

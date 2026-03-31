
import { useState, useEffect } from 'react';
import Head from 'next/head';
import ActiveSignal from '../components/ActiveSignal'; // আমরা এই কম্পোনেন্টটি পুনরায় ব্যবহার করব

export default function Home() {
  // সিগন্যাল ডেটা এবং লোডিং স্টেট রাখার জন্য State
  const [signal, setSignal] = useState(null);
  const [loading, setLoading] = useState(true);

  // API থেকে ডেটা আনার জন্য ফাংশন
  const fetchSignal = async () => {
    try {
      const response = await fetch('/api/index');
      const data = await response.json();
      
      // যদি API থেকে কোনো শক্তিশালী সিগন্যাল আসে, তবে প্রথমটি সেট করুন
      if (data && data.length > 0) {
        setSignal(data[0]); 
      } else {
        setSignal(null); // কোনো সিগন্যাল না থাকলে null সেট করুন
      }
    } catch (error) {
      console.error('Error fetching signal:', error);
      setSignal(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // প্রথমবার লোড হওয়ার সময় ডেটা আনুন
    fetchSignal();

    // প্রতি ১৫ সেকেন্ড পর পর নতুন ডেটার জন্য API কল করুন
    const interval = setInterval(() => {
      fetchSignal();
    }, 15000); // 15 seconds

    // কম্পোনেন্ট আনমাউন্ট হওয়ার সময় ইন্টারভাল পরিষ্কার করুন
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <Head>
        <title>Secure Signal Engine</title>
        <meta name="description" content="High-accuracy manual trading dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex h-screen items-center justify-center bg-gray-900 text-white">
        {
          loading ? (
            <p>Loading Signals...</p>
          ) : signal ? (
            // ActiveSignal কম্পোনেন্টে সিগন্যাল ডেটা পাস করুন
            <ActiveSignal signal={signal} />
          ) : (
            <p>No strong signals at the moment. Waiting for the next scan...</p>
          )
        }
      </main>
    </div>
  );
}

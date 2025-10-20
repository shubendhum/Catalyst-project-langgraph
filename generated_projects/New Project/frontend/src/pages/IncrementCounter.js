import React, { useState, useEffect } from 'react';

const IncrementCounter = () => {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // A mock API call function (if needed)
  const fetchCounterData = async () => {
    setLoading(true);
    try {
      // Simulating an API call
      const response = await new Promise((resolve, reject) => {
        setTimeout(() => {
          resolve({ count: 0 });
        }, 1000);
      });
      // Initialize count from API response
      setCount(response.count);
    } catch (err) {
      setError("Failed to fetch the initial count.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCounterData();
  }, []);

  const handleIncrement = () => {
    setCount(prevCount => prevCount + 1);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen text-xl">Loading...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-screen text-xl text-red-500">{error}</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <h1 className="text-3xl font-bold mb-4">Increment Counter</h1>
      <p className="text-2xl mb-4">Current Count: <span className="text-blue-500">{count}</span></p>
      <button
        onClick={handleIncrement}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition duration-200"
      >
        Increment
      </button>
    </div>
  );
};

export default IncrementCounter;
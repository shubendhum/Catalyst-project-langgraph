import React, { useEffect, useState } from 'react';

const Home = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Simulating an API call
    const fetchData = async () => {
      try {
        // Replace with your API endpoint
        const response = await fetch('https://api.example.com/data');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gray-100">
      <h1 className="text-4xl font-bold text-center mb-4">Welcome to the Home Page</h1>
      <p className="mb-4 text-lg text-gray-700">{description}</p>

      {loading && <p className="text-lg">Loading...</p>}
      {error && <p className="text-lg text-red-500">{error}</p>}

      {data && (
        <div className="w-full max-w-md p-4 bg-white shadow-md rounded-lg">
          <h2 className="text-2xl font-semibold mb-2">Fetched Data:</h2>
          <pre className="whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Home;
import React, { useEffect, useState } from 'react';

const Home = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('https://api.example.com/data'); // Replace with your actual API
        if (!response.ok) {
          throw new Error('Network response was not ok ' + response.statusText);
        }
        const result = await response.json();
        setData(result);
      } catch (error) {
        setError(error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-red-500">
          <h2>Error fetching data: {error.message}</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 bg-white shadow-md rounded-lg mt-10">
      <h1 className="text-3xl font-bold text-center mb-6">Welcome to Our Landing Page</h1>
      <p className="text-lg text-gray-700">
        This is the home page where you can find insightful information and interesting content.
      </p>
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Fetched Data:</h2>
        <pre className="bg-gray-50 p-4 rounded border border-gray-300 overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default Home;
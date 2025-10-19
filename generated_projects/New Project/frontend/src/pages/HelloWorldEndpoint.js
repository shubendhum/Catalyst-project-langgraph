import React, { useEffect, useState } from 'react';

const HelloWorldEndpoint = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHelloWorld = async () => {
      try {
        const response = await fetch('/api/helloworld'); // Update with your actual endpoint if needed
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const result = await response.json();
        setData(result);
      } catch (error) {
        setError(error);
      } finally {
        setLoading(false);
      }
    };

    fetchHelloWorld();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="loader">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <h1 className="text-red-500">Error: {error.message}</h1>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen p-4">
      <h1 className="text-3xl font-bold text-gray-800">{data?.message}</h1>
      <p className="mt-4 text-lg text-gray-600">This is the Hello World endpoint response.</p>
      <button
        onClick={() => alert("Button Clicked!")}
        className="mt-8 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-200"
      >
        Click Me
      </button>
    </div>
  );
};

export default HelloWorldEndpoint;
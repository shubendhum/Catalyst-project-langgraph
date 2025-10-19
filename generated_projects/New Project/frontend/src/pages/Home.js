import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Home = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Simulate fetching data from an API
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Replace with your actual API endpoint
        const response = await axios.get('https://api.example.com/data');
        setData(response.data);
      } catch (err) {
        setError('An error occurred while fetching the data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-4xl font-bold text-center mt-10">Welcome to Our Landing Page!</h1>
      <p className="mt-4 text-center text-lg">
        {data ? data.description : 'No data available.'}
      </p>
      <div className="mt-8 flex flex-col items-center">
        <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
          Get Started
        </button>
      </div>
    </div>
  );
};

export default Home;
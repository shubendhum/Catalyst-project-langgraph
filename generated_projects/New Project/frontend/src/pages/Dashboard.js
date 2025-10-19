import React, { useEffect, useState } from 'react';

// Dummy API endpoint for demonstration
const API_URL = 'https://jsonplaceholder.typicode.com/posts';

const Dashboard = () => {
  const [data, setData] = useState([]); // State to hold the fetched data
  const [loading, setLoading] = useState(true); // State to handle loading
  const [error, setError] = useState(null); // State to handle errors

  // Fetch data from API on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(API_URL);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const result = await response.json();
        setData(result);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-t-4 border-blue-500 border-solid"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-screen">
        <h1 className="text-red-500 text-2xl">Error: {error}</h1>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Main Dashboard</h1>
      <div className="bg-white shadow-md rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-2">Posts</h2>
        <ul className="space-y-4">
          {data.map(post => (
            <li key={post.id} className="border-b border-gray-200 pb-2">
              <h3 className="font-semibold">{post.title}</h3>
              <p className="text-gray-600">{post.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
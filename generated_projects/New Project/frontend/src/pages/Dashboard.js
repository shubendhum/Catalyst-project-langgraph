import React, { useEffect, useState } from 'react';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulating an API call
        const response = await fetch('https://api.example.com/dashboard-data'); // Replace with your actual API endpoint
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

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="loader">Loading...</div> {/* You can replace this with a spinner */}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-500">Error: {error.message}</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Main Dashboard</h1>
      <div className="bg-white shadow-md rounded-lg p-6">
        {data ? (
          <div>
            <h2 className="text-xl font-semibold mb-2">Dashboard Data</h2>
            <pre className="bg-gray-100 p-4 rounded">{JSON.stringify(data, null, 2)}</pre>
          </div>
        ) : (
          <div>No data available</div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
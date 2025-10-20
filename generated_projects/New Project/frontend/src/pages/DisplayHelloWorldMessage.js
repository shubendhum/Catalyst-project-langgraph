import React, { useEffect, useState } from 'react';

const DisplayHelloWorldMessage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        // Simulating an API call (you can replace this with your actual API)
        // const response = await fetch('/api/hello');
        // const data = await response.json();
        // setMessage(data.message);

        // For demo purposes, we'll simulate a delay and then set the message
        setTimeout(() => {
          setMessage('Hello, World!');
          setLoading(false);
        }, 1000);
      } catch (err) {
        setError('Failed to load message');
        setLoading(false);
      }
    };

    fetchMessage();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg font-semibold">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg font-semibold text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gray-100">
      <h1 className="text-3xl font-bold text-center p-5 bg-white rounded-lg shadow-lg">
        {message}
      </h1>
    </div>
  );
};

export default DisplayHelloWorldMessage;
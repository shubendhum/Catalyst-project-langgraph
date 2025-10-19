import React, { useEffect, useState } from 'react';
import axios from 'axios';

const GreetingMessage = () => {
  const [greeting, setGreeting] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        // Replace with your API endpoint
        const response = await axios.get('/api/greeting');
        setGreeting(response.data.greeting);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch greeting message');
        setLoading(false);
      }
    };

    fetchGreeting();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="loader"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen text-center p-4">
      <h1 className="text-3xl font-bold mb-4">Greeting Message</h1>
      <p className="text-xl">{greeting}</p>
    </div>
  );
};

export default GreetingMessage;
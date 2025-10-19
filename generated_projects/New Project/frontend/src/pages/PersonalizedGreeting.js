import React, { useEffect, useState } from 'react';

const PersonalizedGreeting = () => {
  const [greeting, setGreeting] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Mock API call to fetch personalized greeting
    const fetchGreeting = async () => {
      setLoading(true);
      try {
        // Simulating an API call
        const response = await fetch('https://api.example.com/greeting');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setGreeting(data.greeting);
      } catch (err) {
        setError(err.message);
      } finally {
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
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen p-4">
      <h1 className="text-3xl font-bold text-center text-gray-800 mb-4">Personalized Greeting</h1>
      <p className="text-lg text-gray-700">{greeting}</p>
    </div>
  );
};

export default PersonalizedGreeting;
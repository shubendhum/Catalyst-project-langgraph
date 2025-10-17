import React, { useState, useEffect } from 'react';
import GreetingDisplay from '../components/GreetingDisplay';
import GreetingForm from '../components/GreetingForm';
import GreetingHistory from '../components/GreetingHistory';
import ThemeToggle from '../components/ThemeToggle';

const HomePage = () => {
  const [greeting, setGreeting] = useState('');
  const [greetingHistory, setGreetingHistory] = useState([]);
  const [loading, setLoading] = useState({
    default: true,
    personalized: false,
    history: true,
    save: false,
  });
  const [error, setError] = useState({
    default: null,
    personalized: null,
    history: null,
    save: null,
  });
  const [name, setName] = useState('');

  // Fetch default greeting on initial load
  useEffect(() => {
    const fetchDefaultGreeting = async () => {
      try {
        const response = await getDefaultGreeting();
        setGreeting(response.greeting);
        setError({ ...error, default: null });
      } catch (err) {
        setError({ ...error, default: 'Failed to load default greeting' });
      } finally {
        setLoading({ ...loading, default: false });
      }
    };

    // Fetch greeting history on initial load
    const fetchGreetingHistory = async () => {
      try {
        const response = await getGreetingHistory();
        setGreetingHistory(response.history);
        setError({ ...error, history: null });
      } catch (err) {
        setError({ ...error, history: 'Failed to load greeting history' });
      } finally {
        setLoading({ ...loading, history: false });
      }
    };

    fetchDefaultGreeting();
    fetchGreetingHistory();
  }, []);

  // Handler for form submission to get personalized greeting
  const handleGreetingRequest = async (name) => {
    setName(name);
    setLoading({ ...loading, personalized: true });
    
    try {
      const response = await getPersonalizedGreeting(name);
      setGreeting(response.greeting);
      setError({ ...error, personalized: null });
    } catch (err) {
      setError({ ...error, personalized: 'Failed to get personalized greeting' });
    } finally {
      setLoading({ ...loading, personalized: false });
    }
  };

  // Handler for saving greeting
  const handleSaveGreeting = async () => {
    if (!greeting || !name) return;
    
    setLoading({ ...loading, save: true });
    
    try {
      await saveGreeting({ name, greeting });
      
      // Refresh greeting history after saving
      const response = await getGreetingHistory();
      setGreetingHistory(response.history);
      setError({ ...error, save: null });
    } catch (err) {
      setError({ ...error, save: 'Failed to save greeting' });
    } finally {
      setLoading({ ...loading, save: false });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Greeting App</h1>
          <ThemeToggle />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <GreetingDisplay 
                greeting={greeting} 
                loading={loading.default || loading.personalized}
                error={error.default || error.personalized}
              />
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <GreetingForm 
                onSubmit={handleGreetingRequest} 
                onSave={handleSaveGreeting}
                loading={loading.personalized || loading.save}
                saveError={error.save}
                disabled={loading.default}
              />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 h-full">
            <GreetingHistory 
              history={greetingHistory}
              loading={loading.history}
              error={error.history}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Mock API functions (replace with actual implementations)
const getDefaultGreeting = async () => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ greeting: "Hello, welcome to our greeting app!" });
    }, 500);
  });
};

const getPersonalizedGreeting = async (name) => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ greeting: `Hello, ${name}! Nice to meet you.` });
    }, 800);
  });
};

const saveGreeting = async (data) => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 600);
  });
};

const getGreetingHistory = async () => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        history: [
          { id: 1, name: "John", greeting: "Hello, John! Nice to meet you.", timestamp: new Date().toISOString() },
          { id: 2, name: "Sarah", greeting: "Hello, Sarah! Nice to meet you.", timestamp: new Date(Date.now() - 3600000).toISOString() },
          { id: 3, name: "Miguel", greeting: "Hello, Miguel! Nice to meet you.", timestamp: new Date(Date.now() - 86400000).toISOString() },
        ]
      });
    }, 700);
  });
};

export default HomePage;
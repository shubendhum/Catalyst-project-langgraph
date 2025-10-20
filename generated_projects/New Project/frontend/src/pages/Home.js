import React, { useEffect, useState } from 'react';

const Home = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('https://api.example.com/data'); // Replace with your API URL
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

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-100">
                <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full border-t-transparent border-blue-500" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen bg-red-100">
                <h2 className="text-red-600">Error: {error}</h2>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-4">
            <h1 className="text-4xl font-bold text-center mb-4">Welcome to Our Landing Page</h1>
            <p className="text-lg text-center mb-8">This is a beautifully crafted landing page with a responsive design.</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {data && data.map((item) => (
                    <div key={item.id} className="p-4 border rounded-lg shadow-lg bg-white">
                        <h2 className="text-2xl font-semibold">{item.title}</h2>
                        <p className="text-gray-600">{item.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Home;
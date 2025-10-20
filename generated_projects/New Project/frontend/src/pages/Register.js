import React, { useState } from 'react';
import axios from 'axios';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const { username, email, password } = formData;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/register', formData);
      setSuccess(response.data.message);
      setFormData({ username: '', email: '', password: '' }); // Reset form
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Register</h2>
      
      {loading && <p className="text-blue-500">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {success && <p className="text-green-500">{success}</p>}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium">Username</label>
          <input
            type="text"
            name="username"
            value={username}
            onChange={handleChange}
            required
            className="mt-1 p-2 border border-gray-300 rounded-md w-full"
          />
        </div>
        
        <div>
          <label htmlFor="email" className="block text-sm font-medium">Email</label>
          <input
            type="email"
            name="email"
            value={email}
            onChange={handleChange}
            required
            className="mt-1 p-2 border border-gray-300 rounded-md w-full"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium">Password</label>
          <input
            type="password"
            name="password"
            value={password}
            onChange={handleChange}
            required
            className="mt-1 p-2 border border-gray-300 rounded-md w-full"
          />
        </div>

        <button type="submit" disabled={loading} className="w-full p-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md">
          Register
        </button>
      </form>

      <div className="mt-4 text-center">
        <p className="text-sm">Already have an account? <a href="/login" className="text-blue-600">Log in</a></p>
      </div>
    </div>
  );
};

export default Register;
import axios from 'axios';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:3000', // Use environment variable or localhost
});

// Request interceptor for adding JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt'); // Replace with your token storage method
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => {
    return response.data; // Return only the data part of the response
  },
  (error) => {
    const { response } = error;
    
    if (response) {
      const status = response.status;

      if (status === 404) {
        alert('Error: Message not found');
      } else if (status === 400) {
        alert('Error: Invalid input');
      } else {
        alert(`Error: ${response.status} - ${response.statusText}`);
      }
    } else {
      alert('Network Error');
    }

    return Promise.reject(error);
  }
);

// API methods
const apiService = {
  getMessage: async () => {
    try {
      return await apiClient.get('/api/message');
    } catch (error) {
      // Error handling is already implemented in response interceptor
      throw error;
    }
  },

  postMessage: async (content) => {
    if (typeof content !== 'string' || content.trim() === '') {
      throw new Error('Invalid input: content should be a non-empty string.');
    }

    try {
      return await apiClient.post('/api/message', { content });
    } catch (error) {
      // Error handling is already implemented in response interceptor
      throw error;
    }
  }
};

export default apiService;
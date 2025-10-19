import axios from 'axios';

// Create an Axios instance with a base URL from the environment
const apiClient = axios.create({
  baseURL: process.env.API_BASE_URL, // Ensure you set API_BASE_URL in your environment variables
  headers: {
    'Content-Type': 'application/json',
  },
});

// Axios request interceptor to add the Bearer token for authentication
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token'); // Assume the token is stored in local storage
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Axios response interceptor to handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;
    if (response) {
      const statusCode = response.status;
      switch (statusCode) {
        case 400:
          // Handle Bad Request
          console.error('Bad Request: ', response.data);
          break;
        case 401:
          // Handle Unauthorized
          console.error('Unauthorized: ', response.data);
          break;
        case 500:
          // Handle Server Error
          console.error('Server Error: ', response.data);
          break;
        default:
          console.error('An error occurred: ', response.data);
      }
    } else {
      // General network error
      console.error('Network Error: ', error.message);
    }
    return Promise.reject(error);
  }
);

// API Service Class
class ApiService {
  // Method to submit a user's name and get a greeting
  async greetUser(name) {
    try {
      const response = await apiClient.post('/api/greet', { body: { name } });
      return response.data; // Returns { message: string }
    } catch (error) {
      console.error("Failed to greet user", error);
      throw error; // Rethrow the error to handle it further if needed
    }
  }

  // Method to get a default greeting message
  async getDefaultGreeting() {
    try {
      const response = await apiClient.get('/api/greet');
      return response.data; // Returns { message: string }
    } catch (error) {
      console.error("Failed to get default greeting", error);
      throw error; // Rethrow the error to handle it further if needed
    }
  }
}

export default new ApiService();
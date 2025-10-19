import axios from 'axios';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:3000', // Use environment variable or default to localhost
  timeout: 10000, // Optional: Set a timeout for requests
});

// Add a request interceptor
apiClient.interceptors.request.use(
  config => {
    // You can add an authorization header with the token if it exists
    const token = localStorage.getItem('jwt_token'); // Fetch token from local storage or any other storage
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config; // Return the modified config
  },
  error => {
    return Promise.reject(error); // Handle request error
  }
);

// Add a response interceptor
apiClient.interceptors.response.use(
  response => {
    return response.data; // Return the data from the response
  },
  error => {
    // Handle errors based on status codes
    const status = error.response ? error.response.status : null;
    if (status === 400) {
      console.error('Bad Request:', error.response.data.message);
    } else if (status === 500) {
      console.error('Server Error:', error.response.data.message);
    } else {
      console.error('An unexpected error occurred:', error);
    }
    return Promise.reject(error); // Return a rejected promise for further handling
  }
);

// API service methods

const ApiService = {
  // GET method for /api/greet
  greet: async () => {
    try {
      const response = await apiClient.get('/api/greet');
      return response; // Will be { message: "Hello World" }
    } catch (error) {
      throw error; // Rethrow for further handling
    }
  },

  // POST method for /api/greet
  greetWithName: async (name) => {
    if (!name || typeof name !== 'string') {
      throw new Error("Bad Request - Name is required");
    }
    
    try {
      const response = await apiClient.post('/api/greet', { name });
      return response; // Will be { message: "Hello, {name}" }
    } catch (error) {
      throw error; // Rethrow for further handling
    }
  }
};

export default ApiService;
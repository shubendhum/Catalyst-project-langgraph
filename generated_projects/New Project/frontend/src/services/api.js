// api-client.js
import axios from 'axios';

/**
 * API client for the Greeting API
 */
class GreetingApiClient {
  /**
   * Initialize the API client
   * @param {Object} config - Configuration options
   * @param {string} [config.baseURL] - Base URL for API calls (defaults to env variable)
   * @param {string} [config.token] - JWT token for authentication
   * @param {Function} [config.onAuthError] - Callback when authentication error occurs
   */
  constructor(config = {}) {
    this.baseURL = config.baseURL || process.env.REACT_APP_API_URL || '/';
    this.token = config.token || localStorage.getItem('jwt_token');
    this.onAuthError = config.onAuthError || (() => {});

    // Create axios instance
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // Setup request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Setup response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          // Handle auth errors
          this.onAuthError(error);
        }
        return Promise.reject(this._formatError(error));
      }
    );
  }

  /**
   * Set JWT token for authentication
   * @param {string} token - JWT token
   */
  setToken(token) {
    this.token = token;
    localStorage.setItem('jwt_token', token);
  }

  /**
   * Clear JWT token
   */
  clearToken() {
    this.token = null;
    localStorage.removeItem('jwt_token');
  }

  /**
   * Format error response for consistency
   * @param {Error} error - Axios error
   * @returns {Object} Formatted error
   * @private
   */
  _formatError(error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      return {
        status: error.response.status,
        data: error.response.data,
        message: error.response.data?.detail || 'An error occurred',
        originalError: error,
      };
    } else if (error.request) {
      // The request was made but no response was received
      return {
        status: 0,
        data: null,
        message: 'No response received from server',
        originalError: error,
      };
    } else {
      // Something happened in setting up the request that triggered an Error
      return {
        status: 0,
        data: null,
        message: error.message || 'Unknown error occurred',
        originalError: error,
      };
    }
  }

  /**
   * Get a default hello world greeting
   * @returns {Promise<{message: string}>} Greeting message
   */
  async getDefaultGreeting() {
    try {
      const response = await this.client.get('/api/greeting');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get a personalized greeting
   * @param {string} name - Person's name
   * @returns {Promise<{message: string}>} Personalized greeting message
   */
  async getPersonalizedGreeting(name) {
    if (!name) {
      throw new Error('Name is required');
    }

    try {
      const response = await this.client.get(`/api/greeting/${encodeURIComponent(name)}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Save a new greeting to the database
   * @param {Object} data - Greeting data
   * @param {string} data.name - Name for the greeting
   * @returns {Promise<{id: string, name: string, message: string, timestamp: string}>} Created greeting
   */
  async createGreeting(data) {
    if (!data.name) {
      throw new Error('Name is required');
    }

    try {
      const response = await this.client.post('/api/greeting', data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get history of saved greetings
   * @returns {Promise<{greetings: Array<{id: string, name: string, message: string, timestamp: string}>}>} List of greetings
   */
  async getGreetingHistory() {
    try {
      const response = await this.client.get('/api/greetings');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

export default GreetingApiClient;
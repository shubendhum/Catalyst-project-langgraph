import axios from 'axios';

/**
 * TodoAPI Client Service
 * 
 * A complete API client for the Todo application with authentication support,
 * error handling, and all API endpoints implemented.
 */
class TodoApiService {
  constructor(baseURL = process.env.API_BASE_URL || 'http://localhost:8000') {
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for adding auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for handling errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        const customError = {
          statusCode: error.response?.status || 500,
          message: error.response?.data?.message || 'An unexpected error occurred',
          data: error.response?.data || {},
          originalError: error,
        };

        // Handle token expiration
        if (customError.statusCode === 401) {
          // Clear the token from storage
          this.clearAuthToken();
          
          // You can add logic to redirect to login or refresh token here
          // e.g., window.location.href = '/login';
        }

        return Promise.reject(customError);
      }
    );
  }

  /**
   * Authentication token management
   */
  getAuthToken() {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  setAuthToken(token, remember = false) {
    if (remember) {
      localStorage.setItem('auth_token', token);
    } else {
      sessionStorage.setItem('auth_token', token);
    }
  }

  clearAuthToken() {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  /**
   * Get all todo items with optional filtering
   * 
   * @param {Object} options - Filter options
   * @param {boolean} [options.completed] - Filter by completion status
   * @param {string} [options.priority] - Filter by priority
   * @returns {Promise<Array>} Array of todo items
   */
  async getAllTodos({ completed, priority } = {}) {
    try {
      const params = {};
      
      if (completed !== undefined) {
        params.completed = completed;
      }
      
      if (priority) {
        params.priority = priority;
      }
      
      const response = await this.api.get('/api/todos', { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch todos');
    }
  }

  /**
   * Get a specific todo item by ID
   * 
   * @param {string} todoId - ID of the todo to retrieve
   * @returns {Promise<Object>} Todo item
   */
  async getTodoById(todoId) {
    try {
      if (!todoId) {
        throw new Error('Todo ID is required');
      }

      const response = await this.api.get(`/api/todos/${todoId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `Failed to fetch todo with ID: ${todoId}`);
    }
  }

  /**
   * Create a new todo item
   * 
   * @param {Object} todoData - Data for the new todo
   * @param {string} todoData.title - Title of the todo
   * @param {string} todoData.description - Description of the todo
   * @param {string} [todoData.priority] - Priority level (optional)
   * @param {string|Date} [todoData.due_date] - Due date (optional)
   * @returns {Promise<Object>} Created todo item
   */
  async createTodo({ title, description, priority, due_date }) {
    try {
      if (!title || !description) {
        throw new Error('Title and description are required');
      }

      const todoData = {
        title,
        description,
        ...(priority && { priority }),
        ...(due_date && { due_date }),
      };

      const response = await this.api.post('/api/todos', todoData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to create todo');
    }
  }

  /**
   * Update an existing todo item
   * 
   * @param {string} todoId - ID of the todo to update
   * @param {Object} updateData - Fields to update
   * @param {string} [updateData.title] - Updated title
   * @param {string} [updateData.description] - Updated description
   * @param {boolean} [updateData.completed] - Updated completion status
   * @param {string} [updateData.priority] - Updated priority
   * @param {string|Date} [updateData.due_date] - Updated due date
   * @returns {Promise<Object>} Updated todo item
   */
  async updateTodo(todoId, updateData = {}) {
    try {
      if (!todoId) {
        throw new Error('Todo ID is required');
      }

      if (Object.keys(updateData).length === 0) {
        throw new Error('At least one field must be provided for update');
      }

      const response = await this.api.put(`/api/todos/${todoId}`, updateData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `Failed to update todo with ID: ${todoId}`);
    }
  }

  /**
   * Delete a todo item
   * 
   * @param {string} todoId - ID of the todo to delete
   * @returns {Promise<void>}
   */
  async deleteTodo(todoId) {
    try {
      if (!todoId) {
        throw new Error('Todo ID is required');
      }

      await this.api.delete(`/api/todos/${todoId}`);
      return true;
    } catch (error) {
      throw this.handleError(error, `Failed to delete todo with ID: ${todoId}`);
    }
  }

  /**
   * Toggle the completion status of a todo item
   * 
   * @param {string} todoId - ID of the todo to toggle
   * @returns {Promise<Object>} Updated todo item
   */
  async toggleTodoCompletion(todoId) {
    try {
      if (!todoId) {
        throw new Error('Todo ID is required');
      }

      const response = await this.api.patch(`/api/todos/${todoId}/complete`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `Failed to toggle completion for todo with ID: ${todoId}`);
    }
  }

  /**
   * Handle API errors
   * 
   * @param {Error} error - The error object
   * @param {string} defaultMessage - Default error message
   * @returns {Error} Formatted error object
   */
  handleError(error, defaultMessage = 'An error occurred') {
    if (error.statusCode) {
      // This is already our custom error from the interceptor
      error.message = error.message || defaultMessage;
      return error;
    }
    
    // For errors not caught by the interceptor
    return {
      statusCode: 500,
      message: defaultMessage,
      originalError: error,
    };
  }
}

// Export as a singleton instance
export const todoApi = new TodoApiService();

// Also export the class for testing or custom instantiation
export default TodoApiService;
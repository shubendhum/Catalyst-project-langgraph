// App.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App'; // Adjust the path based on your folder structure
import * as api from './api'; // Import your API functions

// Mock the API function for authentication
jest.mock('./api');

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test
  });

  it('renders the Home page at the root path', () => {
    render(
      <Router>
        <App />
      </Router>
    );

    expect(screen.getByText(/welcome to the home page/i)).toBeInTheDocument(); // Adjust according to your Home component
  });

  it('navigates to protected route when authenticated', async () => {
    // Mock the API call to simulate successful authentication
    api.authenticateUser.mockResolvedValueOnce({ success: true });

    render(
      <Router>
        <App />
      </Router>
    );

    // Simulate a click to authenticate the user
    fireEvent.click(screen.getByText(/login/i)); // Adjust according to your Login button text

    await waitFor(() => {
      expect(api.authenticateUser).toHaveBeenCalled();
    });

    // Check for the protected component
    expect(screen.getByText(/protected route content/i)).toBeInTheDocument(); // Adjust according to your protected component content
  });

  it('does not allow access to protected route when not authenticated', () => {
    render(
      <Router>
        <App />
      </Router>
    );

    // Attempt to access protected route directly (you may need to replace the path with the actual protected route)
    window.history.pushState({}, 'Protected Route', '/protected');

    render(
      <Router>
        <App />
      </Router>
    );

    // Check for redirect to Home or an unauthorized message
    expect(screen.getByText(/please log in to access this page/i)).toBeInTheDocument(); // Adjust according to your unauthenticated message
  });

  it('renders a loading state while authenticating', async () => {
    // Simulate a pending API call
    api.authenticateUser.mockImplementation(() => new Promise(() => {})); // Never resolve to keep in loading state

    render(
      <Router>
        <App />
      </Router>
    );

    fireEvent.click(screen.getByText(/login/i)); // Adjust according to your Login button text

    // Check for loading state
    expect(screen.getByText(/loading.../i)).toBeInTheDocument(); // Adjust to match your loading text

    // Cleanup pending promise
    api.authenticateUser.mockClear();
  });

  it('shows error message on failed authentication', async () => {
    // Mock the API call to simulate failed authentication
    api.authenticateUser.mockResolvedValueOnce({ success: false, message: 'Invalid credentials' });

    render(
      <Router>
        <App />
      </Router>
    );

    fireEvent.click(screen.getByText(/login/i)); // Adjust according to your Login button text

    await waitFor(() => {
      expect(api.authenticateUser).toHaveBeenCalled();
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument(); // Adjust according to your error message
    });
  });
});
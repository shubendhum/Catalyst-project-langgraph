// App.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router, Route, Routes, MemoryRouter } from 'react-router-dom';
import App from './App'; // Make sure this path matches your project structure
import '@testing-library/jest-dom/extend-expect';
import * as api from './api'; // Adjust the import as needed for your API calls
import { UserProvider } from './UserContext'; // Context for managing user authentication

// Mock the API calls
jest.mock('./api');

// Mock the components for routing
jest.mock('./HomePage', () => {
  return () => <div>Home Page</div>;
});

jest.mock('./ProtectedPage', () => {
  return () => <div>Protected Page</div>;
});

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders HomePage on initial load', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText('Home Page')).toBeInTheDocument();
  });

  test('navigates to ProtectedPage when logged in', async () => {
    api.mockLogin.mockResolvedValue({ success: true });

    render(
      <MemoryRouter initialEntries={['/']}>
        <UserProvider>
          <App />
        </UserProvider>
      </MemoryRouter>
    );

    // Simulate login action
    fireEvent.click(screen.getByText('Login')); // Assumes there's a button for login which triggers the API call

    await waitFor(() => {
      expect(api.mockLogin).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText('Home Page')).toBeInTheDocument(); // Confirm we are still on HomePage
    fireEvent.click(screen.getByText('Go to Protected')); // Assumes a navigation link/button to ProtectedPage

    await waitFor(() => {
      expect(screen.getByText('Protected Page')).toBeInTheDocument();
    });
  });

  test('redirects to login when accessing protected route if not authenticated', async () => {
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <UserProvider>
          <App />
        </UserProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Login to access this page')).toBeInTheDocument(); // Assumes there is a message for redirect
  });

  test('shows error message on failed login', async () => {
    api.mockLogin.mockResolvedValue({ success: false, message: 'Login failed' });

    render(
      <MemoryRouter initialEntries={['/']}>
        <UserProvider>
          <App />
        </UserProvider>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument(); // Assumes an error message is shown
    });
  });
});
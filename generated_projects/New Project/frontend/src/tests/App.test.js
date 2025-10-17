import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import App from './App';
import * as api from './services/api';

// Mock the API calls
jest.mock('./services/api', () => ({
  getDefaultGreeting: jest.fn(),
  getPersonalizedGreeting: jest.fn(),
  saveGreeting: jest.fn(),
  getGreetingHistory: jest.fn(),
}));

// Mock authentication hook or context
jest.mock('./hooks/useAuth', () => ({
  __esModule: true,
  default: () => ({
    isAuthenticated: mockIsAuthenticated,
    login: mockLogin,
    logout: mockLogout,
    user: mockUser,
  }),
}));

// Mock variables for authentication
let mockIsAuthenticated = false;
let mockUser = null;
const mockLogin = jest.fn().mockImplementation(() => {
  mockIsAuthenticated = true;
  mockUser = { id: '123', name: 'Test User' };
  return Promise.resolve({ id: '123', name: 'Test User' });
});
const mockLogout = jest.fn().mockImplementation(() => {
  mockIsAuthenticated = false;
  mockUser = null;
});

describe('App Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Reset authentication state
    mockIsAuthenticated = false;
    mockUser = null;
    
    // Set up API mock returns
    api.getDefaultGreeting.mockResolvedValue({ message: 'Hello, World!' });
    api.getPersonalizedGreeting.mockResolvedValue({ message: 'Hello, Test User!' });
    api.saveGreeting.mockResolvedValue({ success: true });
    api.getGreetingHistory.mockResolvedValue([
      { id: 1, message: 'Hello, World!', timestamp: '2023-01-01T12:00:00Z' },
      { id: 2, message: 'Hello, Test User!', timestamp: '2023-01-02T12:00:00Z' },
    ]);
  });

  test('renders HomePage with default components', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Check if main components are rendered
    expect(await screen.findByTestId('greeting-display')).toBeInTheDocument();
    expect(screen.getByTestId('greeting-form')).toBeInTheDocument();
    expect(screen.getByTestId('theme-toggle')).toBeInTheDocument();
    
    // Default greeting should be loaded
    expect(api.getDefaultGreeting).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.getByTestId('greeting-text')).toHaveTextContent('Hello, World!');
    });
  });

  test('navigation between routes works correctly', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Verify we are on the home page
    expect(await screen.findByTestId('home-page')).toBeInTheDocument();
    
    // Navigate to login page (assuming there's a login link)
    const loginLink = screen.getByText(/login/i);
    userEvent.click(loginLink);
    
    // Verify we are now on the login page
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
    
    // Navigate back to home page
    const homeLink = screen.getByText(/home/i);
    userEvent.click(homeLink);
    
    // Verify we are back on the home page
    expect(await screen.findByTestId('home-page')).toBeInTheDocument();
  });

  test('authentication flow works correctly', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );
    
    // Verify we are on the login page
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
    
    // Fill in login form and submit
    userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    await act(async () => {
      userEvent.click(screen.getByRole('button', { name: /log in/i }));
    });
    
    // Login function should have been called
    expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    
    // User should be redirected to home page after successful login
    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });
    
    // Greeting history should be visible for authenticated users
    expect(screen.getByTestId('greeting-history')).toBeInTheDocument();
    expect(api.getGreetingHistory).toHaveBeenCalled();
    
    // Logout
    const logoutButton = screen.getByText(/logout/i);
    await act(async () => {
      userEvent.click(logoutButton);
    });
    
    // Logout function should have been called
    expect(mockLogout).toHaveBeenCalled();
    
    // Greeting history should not be visible after logout
    await waitFor(() => {
      expect(screen.queryByTestId('greeting-history')).not.toBeInTheDocument();
    });
  });

  test('protected routes redirect to login when not authenticated', async () => {
    render(
      <MemoryRouter initialEntries={['/profile']}>
        <App />
      </MemoryRouter>
    );
    
    // Should be redirected to login page
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
    expect(screen.getByText(/please log in to view this page/i)).toBeInTheDocument();
    
    // Login
    userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    await act(async () => {
      userEvent.click(screen.getByRole('button', { name: /log in/i }));
    });
    
    // After login, should be redirected to the originally requested page (profile)
    await waitFor(() => {
      expect(screen.getByTestId('profile-page')).toBeInTheDocument();
    });
  });

  test('submitting greeting form works correctly', async () => {
    // Set up as authenticated user
    mockIsAuthenticated = true;
    mockUser = { id: '123', name: 'Test User' };
    
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Fill out and submit greeting form
    const nameInput = await screen.findByLabelText(/name/i);
    userEvent.type(nameInput, 'John');
    
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await act(async () => {
      userEvent.click(submitButton);
    });
    
    // API should be called with the correct data
    expect(api.getPersonalizedGreeting).toHaveBeenCalledWith('John');
    expect(api.saveGreeting).toHaveBeenCalled();
    
    // Updated greeting should be displayed
    await waitFor(() => {
      expect(screen.getByTestId('greeting-text')).toHaveTextContent('Hello, Test User!');
    });
    
    // Greeting history should be refreshed
    expect(api.getGreetingHistory).toHaveBeenCalled();
  });

  test('theme toggle works correctly', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Find theme toggle button
    const themeToggle = await screen.findByTestId('theme-toggle');
    
    // App should start with light theme
    expect(document.body).toHaveClass('light-theme');
    
    // Toggle to dark theme
    userEvent.click(themeToggle);
    expect(document.body).toHaveClass('dark-theme');
    
    // Toggle back to light theme
    userEvent.click(themeToggle);
    expect(document.body).toHaveClass('light-theme');
  });
  
  test('handles API errors gracefully', async () => {
    // Mock API to throw an error
    api.getDefaultGreeting.mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Error message should be displayed
    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });
});
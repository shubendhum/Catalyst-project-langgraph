// App.test.js
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter as Router, MemoryRouter } from 'react-router-dom';
import App from './App'; // Adjust the import based on your project structure
import '@testing-library/jest-dom/extend-expect';
import * as api from './api'; // Import your API module for mocking

jest.mock('./api'); // Mock the API module

describe('App Component', () => {
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the Home page on the root path', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/Landing page/i)).toBeInTheDocument();
  });

  test('navigates to the Login page', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Login/i));

    expect(screen.getByText(/Login page/i)).toBeInTheDocument();
  });

  test('navigates to the Register page', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Register/i));

    expect(screen.getByText(/Registration page/i)).toBeInTheDocument();
  });

  test('navigates to the Dashboard page when authenticated', async () => {
    // Mock API call to simulate successful login
    api.loginUser.mockResolvedValueOnce({ token: 'test-token' });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password' } });
    fireEvent.click(screen.getByText(/Submit/i));

    await waitFor(() => expect(api.loginUser).toHaveBeenCalledTimes(1)); 

    // After login, check for dashboard content
    expect(screen.getByText(/Main dashboard/i)).toBeInTheDocument();
  });

  test('redirects to login page when accessing protected routes without authentication', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/Login page/i)).toBeInTheDocument();
    expect(screen.queryByText(/Main dashboard/i)).not.toBeInTheDocument();
  });

  test('navigates to other pages', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Display Hello World Message/i));

    expect(screen.getByText(/Page for Display Hello World Message/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Backend API Endpoint/i));

    expect(screen.getByText(/Page for Backend API Endpoint/i)).toBeInTheDocument();
  });

  // Add more tests as needed for other routes, error handling, etc.
});
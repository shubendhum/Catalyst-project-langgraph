// App.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import App from './App'; // Make sure the correct path is used
import * as api from './api'; // Assuming you have an api.js for API calls
import { AuthProvider } from './AuthContext'; // Assuming you have an AuthContext for managing authentication

// Mock API calls
jest.mock('./api');

const renderWithRouter = (ui, { route = '/' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
};

test('renders Home page at /', () => {
  renderWithRouter(<App />);
  expect(screen.getByText(/Landing page/i)).toBeInTheDocument();
});

test('navigates to Login page', () => {
  renderWithRouter(<App />);

  const loginLink = screen.getByRole('link', { name: /login/i });
  fireEvent.click(loginLink);

  expect(screen.getByText(/login page/i)).toBeInTheDocument();
});

test('navigates to Register page', () => {
  renderWithRouter(<App />);
  
  const registerLink = screen.getByRole('link', { name: /register/i });
  fireEvent.click(registerLink);

  expect(screen.getByText(/registration page/i)).toBeInTheDocument();
});

test('allows user to log in and navigate to Dashboard', async () => {
  api.login.mockResolvedValueOnce({ token: 'mock-token' });

  renderWithRouter(<App />);

  fireEvent.click(screen.getByRole('link', { name: /login/i }));
  
  fireEvent.change(screen.getByPlaceholderText(/username/i), {
    target: { value: 'testuser' },
  });
  fireEvent.change(screen.getByPlaceholderText(/password/i), {
    target: { value: 'password' },
  });
  
  fireEvent.click(screen.getByText(/submit/i));

  await waitFor(() => expect(screen.getByText(/main dashboard/i)).toBeInTheDocument());
});

test('prevents access to Dashboard when not authenticated', () => {
  renderWithRouter(<App />, { route: '/dashboard' });

  expect(screen.getByText(/please log in/i)).toBeInTheDocument(); // Check if login prompt is displayed
});

test('navigates to Personalized Greeting page', async () => {
  renderWithRouter(<App />);

  const personalizedGreetingLink = screen.getByRole('link', { name: /personalized greeting/i });
  fireEvent.click(personalizedGreetingLink);

  expect(screen.getByText(/page for personalized greeting/i)).toBeInTheDocument();
});

test('mock API call in Display Greeting page', async () => {
  api.fetchGreeting.mockResolvedValueOnce({ greeting: 'Hello, User!' });

  renderWithRouter(<App />, { route: '/displaygreeting' });

  await waitFor(() => expect(screen.getByText(/hello, user!/i)).toBeInTheDocument());
});

test('navigates to Responsive Design page', () => {
  renderWithRouter(<App />);
  
  const responsiveDesignLink = screen.getByRole('link', { name: /responsive design/i });
  fireEvent.click(responsiveDesignLink);

  expect(screen.getByText(/page for responsive design/i)).toBeInTheDocument();
});

test('tests Basic Error Handling route', () => {
  renderWithRouter(<App />, { route: '/basicerrorhandling' });
  
  expect(screen.getByText(/page for basic error handling/i)).toBeInTheDocument();
});

// Additional tests can be added for other routes...
// __tests__/Components.test.js

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import LoginForm from '../components/LoginForm';
import RegisterForm from '../components/RegisterForm';
import PersonalizedGreetingCard from '../components/PersonalizedGreetingCard';

// Mock API Call
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ message: 'Success' }),
  })
);

describe('React Components', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  // Test for Navbar
  test('renders Navbar', () => {
    render(<Navbar />);
    expect(screen.getByText(/navigation/i)).toBeInTheDocument();
  });

  // Test for Sidebar
  test('renders Sidebar', () => {
    render(<Sidebar />);
    expect(screen.getByText(/side menu/i)).toBeInTheDocument();
  });

  // Test for LoginForm
  test('renders LoginForm and submits', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'john_doe' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith('/api/login', expect.any(Object));
    });
  });

  // Test for RegisterForm
  test('renders RegisterForm and submits', async () => {
    render(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'jane_doe' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password456' } });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith('/api/register', expect.any(Object));
    });
  });

  // Test for PersonalizedGreetingCard
  test('renders PersonalizedGreetingCard with props', () => {
    const testMessage = 'Happy Birthday, John!';
    render(<PersonalizedGreetingCard message={testMessage} />);
    expect(screen.getByText(testMessage)).toBeInTheDocument();
  });

  // Additional state change test for LoginForm example
  test('LoginForm state changes on input', () => {
    const { getByLabelText } = render(<LoginForm />);
    const usernameInput = getByLabelText(/username/i);
    
    fireEvent.change(usernameInput, { target: { value: 'john_doe' }});
    expect(usernameInput.value).toBe('john_doe');
  });
});
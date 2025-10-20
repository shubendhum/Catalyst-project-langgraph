// components.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';

// Import your components
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import DisplayHelloWorldMessageCard from './DisplayHelloWorldMessageCard';

// Mock API functions for Login and Register
jest.mock('./api', () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
}));

// Test Suite for Navbar
describe('Navbar', () => {
  it('renders Navbar', () => {
    render(<Navbar />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});

// Test Suite for Sidebar
describe('Sidebar', () => {
  it('renders Sidebar', () => {
    render(<Sidebar />);
    expect(screen.getByRole('list')).toBeInTheDocument();
  });
});

// Test Suite for LoginForm
describe('LoginForm', () => {
  beforeEach(() => {
    render(<LoginForm />);
  });

  it('renders LoginForm', () => {
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('calls loginUser API on submit', async () => {
    const { loginUser } = require('./api');
    loginUser.mockResolvedValueOnce({ success: true });

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => expect(loginUser).toHaveBeenCalledWith('testuser', 'password123'));
  });
});

// Test Suite for RegisterForm
describe('RegisterForm', () => {
  beforeEach(() => {
    render(<RegisterForm />);
  });

  it('renders RegisterForm', () => {
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  it('calls registerUser API on submit', async () => {
    const { registerUser } = require('./api');
    registerUser.mockResolvedValueOnce({ success: true });

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'testuser@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => expect(registerUser).toHaveBeenCalledWith('testuser@example.com', 'password123'));
  });
});

// Test Suite for DisplayHelloWorldMessageCard
describe('DisplayHelloWorldMessageCard', () => {
  it('renders message card with correct content', () => {
    render(<DisplayHelloWorldMessageCard />);
    expect(screen.getByText(/hello world/i)).toBeInTheDocument();
  });
});
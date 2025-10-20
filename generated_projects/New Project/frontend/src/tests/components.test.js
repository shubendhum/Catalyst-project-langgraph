import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import IncrementCounterCard from './IncrementCounterCard';

// Mocking any necessary API functions or fetching behavior
jest.mock('axios'); // Example with axios

describe('React Component Tests', () => {
  describe('<Navbar />', () => {
    it('renders the Navbar component', () => {
      render(<Navbar />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('<Sidebar />', () => {
    it('renders the Sidebar component', () => {
      render(<Sidebar />);
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });
  });

  describe('<LoginForm />', () => {
    it('renders the LoginForm component', () => {
      render(<LoginForm />);
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('submits the form with correct data', async () => {
      const loginData = { username: 'testuser', password: 'password' };
      render(<LoginForm />);
      
      fireEvent.change(screen.getByLabelText(/username/i), { target: { value: loginData.username } });
      fireEvent.change(screen.getByLabelText(/password/i), { target: { value: loginData.password } });
      fireEvent.click(screen.getByRole('button', { name: /submit/i }));

      expect(await screen.findByText(/login successful/i)).toBeInTheDocument(); // Example success message
    });

    it('handles API errors', async () => {
      // Mock API call failure
      axios.post.mockImplementationOnce(() => Promise.reject(new Error('API Error')));
      
      render(<LoginForm />);
      fireEvent.click(screen.getByRole('button', { name: /submit/i }));

      expect(await screen.findByText(/login failed/i)).toBeInTheDocument(); // Example failure message
    });
  });

  describe('<RegisterForm />', () => {
    it('renders the RegisterForm component', () => {
      render(<RegisterForm />);
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('submits the form with correct data', async () => {
      const registerData = { email: 'test@test.com', password: 'password' };
      render(<RegisterForm />);
      
      fireEvent.change(screen.getByLabelText(/email/i), { target: { value: registerData.email } });
      fireEvent.change(screen.getByLabelText(/password/i), { target: { value: registerData.password } });
      fireEvent.click(screen.getByRole('button', { name: /register/i }));

      expect(await screen.findByText(/registration successful/i)).toBeInTheDocument(); // Example success
    });
  });

  describe('<IncrementCounterCard />', () => {
    it('renders the IncrementCounterCard component', () => {
      render(<IncrementCounterCard />);
      expect(screen.getByText(/increment counter/i)).toBeInTheDocument(); // Assume there's a heading or label
    });

    it('increments the counter when button is clicked', () => {
      render(<IncrementCounterCard />);
      const incrementButton = screen.getByRole('button', { name: /increment/i });

      fireEvent.click(incrementButton);
      expect(screen.getByText(/current count: 1/i)).toBeInTheDocument(); // Example counter display
    });

    it('decrements the counter when button is clicked', () => {
      render(<IncrementCounterCard />);
      const decrementButton = screen.getByRole('button', { name: /decrement/i });

      fireEvent.click(decrementButton); // Make sure the initial count is 0 before clicking
      expect(screen.getByText(/current count: -1/i)).toBeInTheDocument(); // Example counter display
    });
  });
});
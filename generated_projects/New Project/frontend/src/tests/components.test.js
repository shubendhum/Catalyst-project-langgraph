import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import Home from './Home'; // Adjust the path as necessary
import MessageForm from './MessageForm'; // Adjust the path as necessary

// Mock API function for greeting
jest.mock('./api', () => ({
  fetchGreeting: jest.fn(() => Promise.resolve("Hello from mock API!"))
}));

describe('Home Component', () => {
  beforeEach(() => {
    render(<Home />);
  });

  test('renders greeting message', () => {
    const greetingMessage = screen.getByText(/Welcome to the Greeting App/i);
    expect(greetingMessage).toBeInTheDocument();
  });

  test('renders MessageForm', () => {
    const messageForm = screen.getByRole('form');
    expect(messageForm).toBeInTheDocument();
  });

  test('submits form and displays greeting message', async () => {
    const greetingInput = screen.getByLabelText(/Enter your greeting/i);
    const submitButton = screen.getByRole('button', { name: /Submit/i });

    fireEvent.change(greetingInput, { target: { value: 'Hello World!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const displayMessage = screen.getByText(/Hello World!/i);
      expect(displayMessage).toBeInTheDocument();
    });
  });
});

// Tests for MessageForm Component
describe('MessageForm Component', () => {
  let handleChangeMock;

  beforeEach(() => {
    handleChangeMock = jest.fn();
    render(<MessageForm onGreetingChange={handleChangeMock} />);
  });

  test('renders input and button', () => {
    const input = screen.getByLabelText(/Enter your greeting/i);
    const button = screen.getByRole('button', { name: /Submit/i });

    expect(input).toBeInTheDocument();
    expect(button).toBeInTheDocument();
  });

  test('on input change calls onGreetingChange prop', () => {
    const greetingInput = screen.getByLabelText(/Enter your greeting/i);

    fireEvent.change(greetingInput, { target: { value: 'Hi!' } });
    expect(handleChangeMock).toHaveBeenCalled();
    expect(handleChangeMock).toHaveBeenCalledWith('Hi!');
  });

  test('calls the API and updates state on submit', async () => {
    const greetingInput = screen.getByLabelText(/Enter your greeting/i);
    const submitButton = screen.getByRole('button', { name: /Submit/i });

    fireEvent.change(greetingInput, { target: { value: 'Greetings!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const displayMessage = screen.getByText(/Hello from mock API!/i);
      expect(displayMessage).toBeInTheDocument();
    });
  });
});
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import HelloWorld from './HelloWorld'; // Adjust the import path as necessary
import axios from 'axios';

// Mock the axios module
jest.mock('axios');

describe('HelloWorld Component', () => {
  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test
  });

  test('renders HelloWorld component', () => {
    render(<HelloWorld />);
    const headingElement = screen.getByText(/hello world/i);
    expect(headingElement).toBeInTheDocument();
  });

  test('displays fetched message from API', async () => {
    const message = "Hello, World from API!";
    axios.get.mockResolvedValueOnce({ data: { message } });

    render(<HelloWorld />);

    // Wait for the message to be displayed
    const messageElement = await screen.findByText(message);
    expect(messageElement).toBeInTheDocument();
  });

  test('handles user interactions', async () => {
    const message = "Hello, World from API!";
    axios.get.mockResolvedValueOnce({ data: { message } });

    render(<HelloWorld />);

    // Assume there's a button that fetches the message
    const buttonElement = screen.getByRole('button', { name: /fetch message/i });
    fireEvent.click(buttonElement);

    const messageElement = await screen.findByText(message);
    expect(messageElement).toBeInTheDocument();
  });

  test('component accepts props', () => {
    const mockClassName = "custom-class";
    render(<HelloWorld className={mockClassName} />);
    
    const component = screen.getByText(/hello world/i).closest('div');
    expect(component).toHaveClass(mockClassName);
  });

  test('state changes correctly after fetching', async () => {
    const message = "State changed message!";
    axios.get.mockResolvedValueOnce({ data: { message } });

    render(<HelloWorld />);
    
    // Assume the initial state contains a loading message
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /fetch message/i }));
    
    const messageElement = await screen.findByText(message);
    expect(messageElement).toBeInTheDocument();
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
});
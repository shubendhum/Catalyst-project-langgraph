// App.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import App from './App'; // Adjust the import path based on your file structure
import * as api from './api'; // Assuming `api.js` contains your API calls

// Mock the API calls
jest.mock('./api');

describe('App Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
  });

  test('renders home page on default route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/Landing page/i)).toBeInTheDocument();
  });

  test('navigates to login page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Login/i));
    expect(screen.getByText(/Login page/i)).toBeInTheDocument();
  });

  test('navigates to register page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Register/i));
    expect(screen.getByText(/Registration page/i)).toBeInTheDocument();
  });

  test('navigates to dashboard when authenticated', async () => {
    api.checkAuth.mockResolvedValueOnce(true); // Mock authenticated API response
    
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Login/i));
    await waitFor(() => {
      expect(screen.getByText(/Main dashboard/i)).toBeInTheDocument();
    });
  });

  test('redirects to login when accessing protected route', async () => {
    api.checkAuth.mockResolvedValueOnce(false); // Mock unauthenticated API response
    
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/Login page/i)).toBeInTheDocument();
  });

  test('navigates to increment counter page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Increment Counter/i));
    expect(screen.getByText(/Page for Increment Counter/i)).toBeInTheDocument();
  });

  test('navigates to decrement counter page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Decrement Counter/i));
    expect(screen.getByText(/Page for Decrement Counter/i)).toBeInTheDocument();
  });

  test('navigates to reset counter page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Reset Counter/i));
    expect(screen.getByText(/Page for Reset Counter/i)).toBeInTheDocument();
  });

  test('navigates to display counter value page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Display Counter Value/i));
    expect(screen.getByText(/Page for Display Counter Value/i)).toBeInTheDocument();
  });

  test('navigates to history log page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/History Log/i));
    expect(screen.getByText(/Page for History Log/i)).toBeInTheDocument();
  });
});
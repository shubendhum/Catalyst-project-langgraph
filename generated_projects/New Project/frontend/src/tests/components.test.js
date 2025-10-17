import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock the ThemeProvider and Router components
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }) => <div data-testid="router">{children}</div>
}));

// Mock any theme provider that might be used
jest.mock('../context/ThemeProvider', () => ({
  ThemeProvider: ({ children }) => <div data-testid="theme-provider">{children}</div>
}));

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('router')).toBeInTheDocument();
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
  });
  
  test('initializes with default theme state', () => {
    // This would require exposing theme state for testing
    // or checking for a specific class/attribute that indicates theme
    render(<App />);
    // Example assuming there's a data attribute for theme
    expect(document.body).toHaveAttribute('data-theme', 'light');
  });
  
  test('toggles theme when theme toggle is clicked', () => {
    render(<App />);
    // Find and click theme toggle button
    const themeToggle = screen.getByRole('button', { name: /toggle theme/i });
    themeToggle.click();
    
    // Check if theme changed to dark
    expect(document.body).toHaveAttribute('data-theme', 'dark');
    
    // Click again to toggle back
    themeToggle.click();
    expect(document.body).toHaveAttribute('data-theme', 'light');
  });
});
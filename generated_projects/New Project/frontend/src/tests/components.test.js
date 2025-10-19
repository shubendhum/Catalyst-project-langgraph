// src/__tests__/components.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { act } from 'react-dom/test-utils';

// Import components
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import LoginForm from '../components/LoginForm';
import RegisterForm from '../components/RegisterForm';
import TaskCreationCard from '../components/TaskCreationCard';

// Mock API calls
jest.mock('../services/api', () => ({
  login: jest.fn(),
  register: jest.fn(),
  createTask: jest.fn(),
  getUser: jest.fn()
}));

// Import the mocked API
import { login, register, createTask, getUser } from '../services/api';

// NAVBAR COMPONENT TESTS
describe('Navbar Component', () => {
  const mockProps = {
    title: 'Test App',
    user: { name: 'John Doe' },
    onLogout: jest.fn()
  };

  test('renders correctly with props', () => {
    render(<Navbar {...mockProps} />);
    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  test('renders without user when not logged in', () => {
    render(<Navbar title="Test App" />);
    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
  });

  test('calls logout function when logout button is clicked', () => {
    render(<Navbar {...mockProps} />);
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);
    expect(mockProps.onLogout).toHaveBeenCalledTimes(1);
  });
});

// SIDEBAR COMPONENT TESTS
describe('Sidebar Component', () => {
  const mockItems = [
    { id: 1, name: 'Dashboard', link: '/dashboard' },
    { id: 2, name: 'Tasks', link: '/tasks' },
    { id: 3, name: 'Settings', link: '/settings' }
  ];

  const mockProps = {
    items: mockItems,
    onItemClick: jest.fn(),
    activeItem: 1
  };

  test('renders sidebar with items', () => {
    render(<Sidebar {...mockProps} />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('highlights the active item', () => {
    render(<Sidebar {...mockProps} />);
    const activeItem = screen.getByText('Dashboard');
    expect(activeItem.closest('li')).toHaveClass('active');
  });

  test('calls onItemClick when an item is clicked', () => {
    render(<Sidebar {...mockProps} />);
    const tasksItem = screen.getByText('Tasks');
    fireEvent.click(tasksItem);
    expect(mockProps.onItemClick).toHaveBeenCalledWith(2);
  });

  test('shows collapsed state when toggled', () => {
    render(<Sidebar {...mockProps} collapsible={true} />);
    const collapseButton = screen.getByRole('button', { name: /collapse/i });
    fireEvent.click(collapseButton);
    
    // Check for collapsed class or style changes
    expect(screen.getByTestId('sidebar-container')).toHaveClass('collapsed');
  });
});

// LOGIN FORM COMPONENT TESTS
describe('LoginForm Component', () => {
  const mockProps = {
    onSubmit: jest.fn(),
    onRegisterClick: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form correctly', () => {
    render(<LoginForm {...mockProps} />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(<LoginForm {...mockProps} />);
    
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled();
  });

  test('submits form with valid data', async () => {
    render(<LoginForm {...mockProps} />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  test('shows error message when login fails', async () => {
    login.mockRejectedValue({ message: 'Invalid credentials' });
    
    render(<LoginForm {...mockProps} />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'wrongpassword');
    
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('redirects to register page when register link is clicked', () => {
    render(<LoginForm {...mockProps} />);
    
    const registerLink = screen.getByText(/register/i);
    fireEvent.click(registerLink);
    
    expect(mockProps.onRegisterClick).toHaveBeenCalledTimes(1);
  });
});

// REGISTER FORM COMPONENT TESTS
describe('RegisterForm Component', () => {
  const mockProps = {
    onSubmit: jest.fn(),
    onLoginClick: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders register form correctly', () => {
    render(<RegisterForm {...mockProps} />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(<RegisterForm {...mockProps} />);
    
    const registerButton = screen.getByRole('button', { name: /register/i });
    fireEvent.click(registerButton);
    
    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled();
  });

  test('validates password match', async () => {
    render(<RegisterForm {...mockProps} />);
    
    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/^password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const registerButton = screen.getByRole('button', { name: /register/i });
    
    await userEvent.type(nameInput, 'Test User');
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.type(confirmPasswordInput, 'differentpassword');
    
    fireEvent.click(registerButton);
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled();
  });

  test('submits form with valid data', async () => {
    render(<RegisterForm {...mockProps} />);
    
    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/^password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const registerButton = screen.getByRole('button', { name: /register/i });
    
    await userEvent.type(nameInput, 'Test User');
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.type(confirmPasswordInput, 'password123');
    
    fireEvent.click(registerButton);
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalledWith({
        name: 'Test User',
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  test('redirects to login page when login link is clicked', () => {
    render(<RegisterForm {...mockProps} />);
    
    const loginLink = screen.getByText(/login/i);
    fireEvent.click(loginLink);
    
    expect(mockProps.onLoginClick).toHaveBeenCalledTimes(1);
  });
});

// TASK CREATION CARD COMPONENT TESTS
describe('TaskCreationCard Component', () => {
  const mockProps = {
    onTaskCreate: jest.fn(),
    categories: [
      { id: 1, name: 'Work' },
      { id: 2, name: 'Personal' }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders task creation card correctly', () => {
    render(<TaskCreationCard {...mockProps} />);
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/due date/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(<TaskCreationCard {...mockProps} />);
    
    const createButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });
    
    expect(mockProps.onTaskCreate).not.toHaveBeenCalled();
  });

  test('submits form with valid data', async () => {
    render(<TaskCreationCard {...mockProps} />);
    
    const titleInput = screen.getByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    const createButton = screen.getByRole('button', { name: /create/i });
    
    await userEvent.type(titleInput, 'New Task');
    await userEvent.type(descriptionInput, 'Task description');
    
    // Select category
    await act(async () => {
      fireEvent.change(categorySelect, { target: { value: '1' } });
    });
    
    // Set due date
    await act(async () => {
      fireEvent.change(dueDateInput, { target: { value: '2023-12-31' } });
    });
    
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(mockProps.onTaskCreate).toHaveBeenCalledWith({
        title: 'New Task',
        description: 'Task description',
        categoryId: '1',
        dueDate: '2023-12-31'
      });
    });
  });

  test('shows success message after task creation', async () => {
    createTask.mockResolvedValue({ id: 123, title: 'New Task' });
    
    render(<TaskCreationCard {...mockProps} />);
    
    const titleInput = screen.getByLabelText(/title/i);
    const createButton = screen.getByRole('button', { name: /create/i });
    
    await userEvent.type(titleInput, 'New Task');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(screen.getByText(/task created successfully/i)).toBeInTheDocument();
    });
  });

  test('shows error message when task creation fails', async () => {
    createTask.mockRejectedValue({ message: 'Server error' });
    
    render(<TaskCreationCard {...mockProps} />);
    
    const titleInput = screen.getByLabelText(/title/i);
    const createButton = screen.getByRole('button', { name: /create/i });
    
    await userEvent.type(titleInput, 'New Task');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
  });
});
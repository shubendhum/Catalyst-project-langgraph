import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import App from './App';
import { AuthProvider } from './contexts/AuthContext'; // Assuming you have an AuthContext

// Mock API server
const server = setupServer(
  // Auth endpoints
  rest.post('/api/login', (req, res, ctx) => {
    const { email, password } = req.body;
    if (email === 'test@example.com' && password === 'password123') {
      return res(ctx.json({ success: true, token: 'fake-auth-token', user: { id: 1, name: 'Test User', email } }));
    }
    return res(ctx.status(401), ctx.json({ success: false, message: 'Invalid credentials' }));
  }),
  
  rest.post('/api/register', (req, res, ctx) => {
    return res(ctx.json({ success: true, token: 'fake-auth-token', user: { id: 2, name: req.body.name, email: req.body.email } }));
  }),

  // Task endpoints
  rest.get('/api/tasks', (req, res, ctx) => {
    return res(ctx.json({
      tasks: [
        { id: 1, title: 'Task 1', description: 'Description 1', completed: false },
        { id: 2, title: 'Task 2', description: 'Description 2', completed: true },
      ]
    }));
  }),

  rest.post('/api/tasks', (req, res, ctx) => {
    return res(ctx.json({ success: true, task: { id: 3, ...req.body, completed: false } }));
  })
);

// Setup and teardown MSW
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Helper function to render the App with Router and AuthProvider
const renderApp = (initialRoute = '/') => {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        <App />
      </MemoryRouter>
    </AuthProvider>
  );
};

describe('App routing', () => {
  test('renders home page by default', () => {
    renderApp();
    expect(screen.getByText(/welcome to the task manager/i)).toBeInTheDocument();
  });

  test('navigates to login page', () => {
    renderApp();
    const loginLink = screen.getByText(/login/i);
    fireEvent.click(loginLink);
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('navigates to register page', () => {
    renderApp();
    const registerLink = screen.getByText(/register/i);
    fireEvent.click(registerLink);
    expect(screen.getByText(/create account/i)).toBeInTheDocument();
  });

  test('redirects to login when accessing protected route while unauthenticated', () => {
    renderApp('/dashboard');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('renders 404 page for non-existent routes', () => {
    renderApp('/non-existent-route');
    expect(screen.getByText(/page not found/i)).toBeInTheDocument();
  });
});

describe('Authentication flow', () => {
  test('successfully logs in user and redirects to dashboard', async () => {
    renderApp('/login');
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/welcome to your dashboard/i)).toBeInTheDocument();
    });
  });

  test('shows error message on failed login', async () => {
    renderApp('/login');
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'wrong@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('successfully registers user and redirects to dashboard', async () => {
    renderApp('/register');
    
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'New User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'newuser@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'newpassword123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'newpassword123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/welcome to your dashboard/i)).toBeInTheDocument();
    });
  });

  test('logs out user and redirects to home page', async () => {
    // First login
    renderApp('/login');
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/welcome to your dashboard/i)).toBeInTheDocument();
    });
    
    // Then logout
    const logoutButton = screen.getByRole('button', { name: /log out/i });
    fireEvent.click(logoutButton);
    
    await waitFor(() => {
      expect(screen.getByText(/welcome to the task manager/i)).toBeInTheDocument();
    });
  });
});

describe('Task pages', () => {
  beforeEach(async () => {
    // Login before each test
    renderApp('/login');
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/welcome to your dashboard/i)).toBeInTheDocument();
    });
  });

  test('navigates to task creation page', () => {
    const createTaskLink = screen.getByText(/create task/i);
    fireEvent.click(createTaskLink);
    expect(screen.getByText(/create a new task/i)).toBeInTheDocument();
  });

  test('creates a new task', async () => {
    // Navigate to task creation page
    const createTaskLink = screen.getByText(/create task/i);
    fireEvent.click(createTaskLink);
    
    // Fill out the form
    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: 'New Test Task' } });
    fireEvent.change(screen.getByLabelText(/description/i), { target: { value: 'This is a test task' } });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    // Verify success message or redirect
    await waitFor(() => {
      expect(screen.getByText(/task created successfully/i)).toBeInTheDocument();
    });
  });

  test('displays task listing', async () => {
    // Navigate to task listing page
    const taskListingLink = screen.getByText(/view tasks/i);
    fireEvent.click(taskListingLink);
    
    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  test('marks a task as complete', async () => {
    // Navigate to task listing page
    const taskListingLink = screen.getByText(/view tasks/i);
    fireEvent.click(taskListingLink);
    
    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });
    
    // Add a handler for completing tasks
    server.use(
      rest.patch('/api/tasks/1/complete', (req, res, ctx) => {
        return res(ctx.json({ success: true, task: { id: 1, title: 'Task 1', description: 'Description 1', completed: true } }));
      })
    );
    
    // Mark task as complete
    const completeButton = screen.getByRole('button', { name: /complete/i, closest: true });
    fireEvent.click(completeButton);
    
    // Verify task is marked as completed
    await waitFor(() => {
      expect(screen.getByText(/task completed/i)).toBeInTheDocument();
    });
  });

  test('edits a task', async () => {
    // Navigate to task listing page
    const taskListingLink = screen.getByText(/view tasks/i);
    fireEvent.click(taskListingLink);
    
    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });
    
    // Add a handler for editing tasks
    server.use(
      rest.put('/api/tasks/1', (req, res, ctx) => {
        return res(ctx.json({ 
          success: true, 
          task: { 
            id: 1, 
            title: req.body.title || 'Updated Task', 
            description: req.body.description || 'Updated Description', 
            completed: false 
          } 
        }));
      })
    );
    
    // Click edit button
    const editButton = screen.getByRole('button', { name: /edit/i, closest: true });
    fireEvent.click(editButton);
    
    // Fill the edit form
    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: 'Updated Task Title' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify the task was updated
    await waitFor(() => {
      expect(screen.getByText(/task updated successfully/i)).toBeInTheDocument();
    });
  });

  test('deletes a task', async () => {
    // Navigate to task listing page
    const taskListingLink = screen.getByText(/view tasks/i);
    fireEvent.click(taskListingLink);
    
    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });
    
    // Add a handler for deleting tasks
    server.use(
      rest.delete('/api/tasks/1', (req, res, ctx) => {
        return res(ctx.json({ success: true }));
      })
    );
    
    // Click delete button
    const deleteButton = screen.getByRole('button', { name: /delete/i, closest: true });
    fireEvent.click(deleteButton);
    
    // Confirm deletion in the modal
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    // Verify the task was deleted
    await waitFor(() => {
      expect(screen.getByText(/task deleted successfully/i)).toBeInTheDocument();
    });
  });
});

describe('Protected routes', () => {
  test('dashboard is protected and redirects to login when unauthenticated', () => {
    renderApp('/dashboard');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('task creation page is protected', () => {
    renderApp('/taskcreation');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('task listing page is protected', () => {
    renderApp('/tasklisting');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('task completion page is protected', () => {
    renderApp('/taskcompletion');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('task deletion page is protected', () => {
    renderApp('/taskdeletion');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('task editing page is protected', () => {
    renderApp('/taskediting');
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('authenticated user can access protected routes', async () => {
    // First login
    renderApp('/login');
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Verify dashboard is accessible after login
    await waitFor(() => {
      expect(screen.getByText(/welcome to your dashboard/i)).toBeInTheDocument();
    });
    
    // Navigate to task creation page
    const createTaskLink = screen.getByText(/create task/i);
    fireEvent.click(createTaskLink);
    expect(screen.getByText(/create a new task/i)).toBeInTheDocument();
  });
});
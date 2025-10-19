import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import TaskCreation from './pages/TaskCreation';
import TaskListing from './pages/TaskListing';
import TaskCompletion from './pages/TaskCompletion';
import TaskDeletion from './pages/TaskDeletion';
import TaskEditing from './pages/TaskEditing';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <div className="container mx-auto px-4 py-8">
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected routes */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/taskcreation" 
                element={
                  <ProtectedRoute>
                    <TaskCreation />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/tasklisting" 
                element={
                  <ProtectedRoute>
                    <TaskListing />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/taskcompletion" 
                element={
                  <ProtectedRoute>
                    <TaskCompletion />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/taskdeletion" 
                element={
                  <ProtectedRoute>
                    <TaskDeletion />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/taskediting" 
                element={
                  <ProtectedRoute>
                    <TaskEditing />
                  </ProtectedRoute>
                } 
              />
              
              {/* Fallback route for non-existent paths */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
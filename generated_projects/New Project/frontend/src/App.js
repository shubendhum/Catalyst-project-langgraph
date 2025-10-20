import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './AuthContext'; // import the Auth Context
import Navbar from './Navbar'; // import the Navbar component

// Your Page Components
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import IncrementCounter from './pages/IncrementCounter';
import DecrementCounter from './pages/DecrementCounter';
import ResetCounter from './pages/ResetCounter';
import DisplayCounterValue from './pages/DisplayCounterValue';
import HistoryLog from './pages/HistoryLog';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useContext(AuthContext);
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <div className="container mx-auto px-4">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
            />
            <Route
              path="/incrementcounter"
              element={<ProtectedRoute><IncrementCounter /></ProtectedRoute>}
            />
            <Route
              path="/decrementcounter"
              element={<ProtectedRoute><DecrementCounter /></ProtectedRoute>}
            />
            <Route
              path="/resetcounter"
              element={<ProtectedRoute><ResetCounter /></ProtectedRoute>}
            />
            <Route
              path="/displaycountervalue"
              element={<ProtectedRoute><DisplayCounterValue /></ProtectedRoute>}
            />
            <Route
              path="/historylog"
              element={<ProtectedRoute><HistoryLog /></ProtectedRoute>}
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
import React, { useState } from 'react';
import { Link } from 'react-router-dom'; // Assuming you're using react-router for navigation

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleMenuToggle = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleLogout = () => {
    // Add your logout logic here
    onLogout();
  };

  return (
    <nav className="bg-blue-600 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <img src="logo.png" alt="Logo" className="h-8 w-8 mr-2" />
          <span className="text-white text-lg font-semibold">App Name</span>
        </div>
        <div className="hidden md:flex space-x-4">
          <Link to="/" className="text-white hover:text-gray-200">Home</Link>
          {isAuthenticated && <Link to="/dashboard" className="text-white hover:text-gray-200">Dashboard</Link>}
          {isAuthenticated ? (
            <button onClick={handleLogout} className="text-white hover:text-gray-200">Logout</button>
          ) : (
            <Link to="/login" className="text-white hover:text-gray-200">Login</Link>
          )}
        </div>
        <button onClick={handleMenuToggle} className="md:hidden text-white focus:outline-none">
          {isMenuOpen ? '✖' : '☰'}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-blue-700 mt-2">
          <Link to="/" className="block text-white px-4 py-2">Home</Link>
          {isAuthenticated && <Link to="/dashboard" className="block text-white px-4 py-2">Dashboard</Link>}
          {isAuthenticated ? (
            <button onClick={handleLogout} className="block text-white px-4 py-2">Logout</button>
          ) : (
            <Link to="/login" className="block text-white px-4 py-2">Login</Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
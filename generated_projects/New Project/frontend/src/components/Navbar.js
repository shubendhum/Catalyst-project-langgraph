import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [MobileMenuOpen, setMobileMenuOpen] = useState(false);
  const history = useHistory();

  const handleLogout = () => {
    onLogout();
    history.push('/'); // Redirect to the home page or login
  };

  return (
    <nav className="bg-blue-600 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <img src="/path-to-your-logo.png" alt="Logo" className="h-8 w-8 mr-2" />
          <span className="text-white text-2xl">App Name</span>
        </div>
        <div className="hidden md:flex space-x-4">
          <a href="/" className="text-white hover:bg-blue-500 px-3 py-2 rounded">Home</a>
          {isAuthenticated && (
            <>
              <a href="/dashboard" className="text-white hover:bg-blue-500 px-3 py-2 rounded">Dashboard</a>
              <button onClick={handleLogout} className="text-white hover:bg-blue-500 px-3 py-2 rounded">
                Logout
              </button>
            </>
          )}
        </div>
        <div className="md:hidden">
          <button onClick={() => setMobileMenuOpen(!MobileMenuOpen)} className="text-white focus:outline-none">
            {MobileMenuOpen ? 'Close' : 'Menu'}
          </button>
        </div>
      </div>
      {MobileMenuOpen && (
        <div className="md:hidden bg-blue-600">
          <a href="/" className="block text-white hover:bg-blue-500 px-3 py-2">Home</a>
          {isAuthenticated && (
            <>
              <a href="/dashboard" className="block text-white hover:bg-blue-500 px-3 py-2">Dashboard</a>
              <button onClick={handleLogout} className="block text-white hover:bg-blue-500 px-3 py-2 w-full text-left">
                Logout
              </button>
            </>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
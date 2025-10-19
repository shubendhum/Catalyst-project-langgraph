import React, { useState } from 'react';

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="bg-gray-800 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <img
            src="/path/to/logo.png" // Replace with your logo path
            alt="Logo"
            className="h-8 w-8 mr-2"
          />
          <span className="text-white text-xl">Your App Name</span>
        </div>
        <div className="hidden md:flex space-x-4">
          <a href="/" className="text-white hover:underline">Home</a>
          {isAuthenticated && (
            <>
              <a href="/dashboard" className="text-white hover:underline">Dashboard</a>
              <button
                onClick={onLogout}
                className="text-white hover:underline"
              >
                Logout
              </button>
            </>
          )}
        </div>
        <button
          className="md:hidden text-white focus:outline-none"
          onClick={handleToggle}
        >
          {isOpen ? <span>&times;</span> : <span>&#9776;</span>}
        </button>
      </div>

      {/* Mobile Menu */}
      <div className={`md:hidden bg-gray-700 ${isOpen ? "block" : "hidden"}`}>
        <a href="/" className="block text-white px-4 py-2 hover:bg-gray-600">Home</a>
        {isAuthenticated && (
          <>
            <a href="/dashboard" className="block text-white px-4 py-2 hover:bg-gray-600">Dashboard</a>
            <button
              onClick={onLogout}
              className="block w-full text-left text-white px-4 py-2 hover:bg-gray-600"
            >
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
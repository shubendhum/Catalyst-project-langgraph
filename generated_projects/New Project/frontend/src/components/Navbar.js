import React, { useState } from 'react';

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-gray-800 p-4 flex items-center justify-between">
      {/* Logo and App Name */}
      <div className="flex items-center">
        <img src="/path/to/logo.png" alt="Logo" className="h-8 w-8 mr-2" />
        <span className="text-white text-lg font-bold">MyApp</span>
      </div>

      {/* Desktop Menu */}
      <div className="hidden md:flex space-x-4">
        <a href="/" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded">
          Home
        </a>
        {isAuthenticated && (
          <>
            <a href="/dashboard" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded">
              Dashboard
            </a>
            <button 
              onClick={onLogout} 
              className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded"
            >
              Logout
            </button>
          </>
        )}
      </div>

      {/* Mobile Menu Button */}
      <div className="md:hidden">
        <button
          className="text-gray-300 focus:outline-none"
          onClick={() => setMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
            </svg>
          )}
        </button>
      </div>
      
      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="absolute top-16 left-0 w-full bg-gray-800 md:hidden">
          <a href="/" className="block text-gray-300 hover:bg-gray-700 hover:text-white px-4 py-2">
            Home
          </a>
          {isAuthenticated && (
            <>
              <a href="/dashboard" className="block text-gray-300 hover:bg-gray-700 hover:text-white px-4 py-2">
                Dashboard
              </a>
              <button 
                onClick={onLogout}
                className="block text-gray-300 hover:bg-gray-700 hover:text-white px-4 py-2 w-full text-left"
              >
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
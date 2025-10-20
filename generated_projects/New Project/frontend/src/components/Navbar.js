import React, { useState } from 'react';

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="bg-blue-600 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex-shrink-0 flex items-center">
            <img
              className="h-8 w-8"
              src="/path/to/logo.png" // Replace with your logo path
              alt="Logo"
            />
            <span className="text-white text-xl ml-2">App Name</span>
          </div>
          <div className="hidden md:flex md:items-center">
            <div className="space-x-4">
              <a href="/" className="text-white hover:bg-blue-500 px-3 py-2 rounded-md">
                Home
              </a>
              {isAuthenticated && (
                <a
                  href="/dashboard"
                  className="text-white hover:bg-blue-500 px-3 py-2 rounded-md"
                >
                  Dashboard
                </a>
              )}
              {isAuthenticated && (
                <button
                  onClick={onLogout}
                  className="text-white hover:bg-blue-500 px-3 py-2 rounded-md"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              onClick={handleToggle}
              className="bg-blue-600 inline-flex items-center justify-center p-2 rounded-md text-white hover:text-white focus:outline-none"
              aria-controls="mobile-menu"
              aria-expanded={isOpen}
            >
              <span className="sr-only">Open main menu</span>
              {isOpen ? (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className={`md:hidden ${isOpen ? 'block' : 'hidden'}`} id="mobile-menu">
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          <a href="/" className="text-white block px-3 py-2 rounded-md hover:bg-blue-500">
            Home
          </a>
          {isAuthenticated && (
            <a
              href="/dashboard"
              className="text-white block px-3 py-2 rounded-md hover:bg-blue-500"
            >
              Dashboard
            </a>
          )}
          {isAuthenticated && (
            <button
              onClick={onLogout}
              className="text-white block px-3 py-2 rounded-md hover:bg-blue-500 w-full text-left"
            >
              Logout
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
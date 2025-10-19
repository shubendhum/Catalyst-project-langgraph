import React, { useState } from 'react';

// Simulated authentication state (you'll replace this with your auth logic)
const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(true); // Change this to test
  return { isAuthenticated };
};

const Navbar = () => {
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="bg-gray-800 p-4 flex justify-between items-center">
      <div className="flex items-center">
        <img className="h-8 w-8 mr-3" src="/path/to/logo.png" alt="Logo" /> {/* Replace with your logo path */}
        <span className="text-white text-xl font-semibold">App Name</span>
      </div>

      <div className="hidden md:flex space-x-4">
        <a href="/" className="text-white hover:bg-gray-700 px-3 py-2 rounded">
          Home
        </a>
        {isAuthenticated && (
          <>
            <a href="/dashboard" className="text-white hover:bg-gray-700 px-3 py-2 rounded">
              Dashboard
            </a>
            <a href="/logout" className="text-white hover:bg-gray-700 px-3 py-2 rounded">
              Logout
            </a>
          </>
        )}
      </div>

      {/* Mobile menu button */}
      <div className="md:hidden">
        <button onClick={toggleMenu} className="text-white focus:outline-none">
          {isOpen ? (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"></path>
            </svg>
          )}
        </button>
      </div>
    </nav>
  );
};

const MobileMenu = ({ isOpen, isAuthenticated }) => {
  return (
    <div className={`md:hidden ${isOpen ? "block" : "hidden"} bg-gray-800`}>
      <a href="/" className="block text-white hover:bg-gray-700 px-4 py-2">
        Home
      </a>
      {isAuthenticated && (
        <>
          <a href="/dashboard" className="block text-white hover:bg-gray-700 px-4 py-2">
            Dashboard
          </a>
          <a href="/logout" className="block text-white hover:bg-gray-700 px-4 py-2">
            Logout
          </a>
        </>
      )}
    </div>
  );
};

// Main Navbar component wrapping the mobile menu
const MainNavbar = () => {
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <Navbar />
      <MobileMenu isOpen={isOpen} isAuthenticated={isAuthenticated} />
    </div>
  );
};

export default MainNavbar;
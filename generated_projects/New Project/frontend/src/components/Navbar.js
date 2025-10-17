import { useState, useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext'; // Adjust the import path as needed

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isAuthenticated, logout } = useContext(AuthContext);
  const location = useLocation();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    closeMenu();
  };

  // Function to determine if a link is active
  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-gray-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and app name */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center" onClick={closeMenu}>
              <img
                className="h-8 w-auto mr-3"
                src="/logo.svg"
                alt="App Logo"
              />
              <span className="text-white font-semibold text-lg">AppName</span>
            </Link>
          </div>

          {/* Desktop navigation links */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Home
              </Link>
              <Link
                to="/dashboard"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/dashboard') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Logout
              </button>
            </div>
          )}

          {/* If not authenticated, show login/register */}
          {!isAuthenticated && (
            <div className="hidden md:flex items-center space-x-4">
              <Link
                to="/login"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/login') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Login
              </Link>
              <Link
                to="/register"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive('/register') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Register
              </Link>
            </div>
          )}

          {/* Mobile menu button */}
          <div className="flex items-center -mr-2 md:hidden">
            <button
              onClick={toggleMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
            >
              <span className="sr-only">Open main menu</span>
              {!isMenuOpen ? (
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
                    strokeWidth="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
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
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu, show/hide based on menu state */}
      <div className={`md:hidden ${isMenuOpen ? 'block' : 'hidden'}`}>
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          {isAuthenticated ? (
            <>
              <Link
                to="/"
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive('/') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                onClick={closeMenu}
              >
                Home
              </Link>
              <Link
                to="/dashboard"
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive('/dashboard') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                onClick={closeMenu}
              >
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive('/login') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                onClick={closeMenu}
              >
                Login
              </Link>
              <Link
                to="/register"
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive('/register') 
                    ? 'text-white bg-gray-900' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                onClick={closeMenu}
              >
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
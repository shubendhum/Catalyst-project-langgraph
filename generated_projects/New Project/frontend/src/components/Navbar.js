import React, { useState } from 'react';

const Navbar = ({ isAuthenticated, onLogout }) => {
    const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);

    const toggleMobileMenu = () => {
        setMobileMenuOpen(!isMobileMenuOpen);
    };

    return (
        <nav className="bg-gray-800 text-white p-4 flex justify-between items-center">
            <div className="flex items-center">
                <img src="/logo.png" alt="Logo" className="h-8 w-8 mr-2" />
                <span className="text-xl font-bold">App Name</span>
            </div>
            <div className="hidden md:flex space-x-4">
                <a href="/" className="hover:underline">Home</a>
                {isAuthenticated && <a href="/dashboard" className="hover:underline">Dashboard</a>}
                {isAuthenticated ? (
                    <button onClick={onLogout} className="hover:underline">Logout</button>
                ) : (
                    <a href="/login" className="hover:underline">Login</a>
                )}
            </div>
            <button
                className="md:hidden p-2"
                onClick={toggleMobileMenu}
            >
                <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>
            {isMobileMenuOpen && (
                <div className="absolute top-16 right-0 bg-gray-800 w-full md:hidden flex flex-col p-4">
                    <a href="/" className="py-2 hover:underline">Home</a>
                    {isAuthenticated && <a href="/dashboard" className="py-2 hover:underline">Dashboard</a>}
                    {isAuthenticated ? (
                        <button onClick={onLogout} className="py-2 hover:underline">Logout</button>
                    ) : (
                        <a href="/login" className="py-2 hover:underline">Login</a>
                    )}
                </div>
            )}
        </nav>
    );
};

export default Navbar;
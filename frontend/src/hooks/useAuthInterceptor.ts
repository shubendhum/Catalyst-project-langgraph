import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface UseAuthInterceptorOptions {
  onAuthRequired?: () => void;
}

/**
 * Auth interceptor hook
 * Automatically detects 401/expired responses and prompts re-authentication
 */
export const useAuthInterceptor = (options: UseAuthInterceptorOptions = {}) => {
  const navigate = useNavigate();

  useEffect(() => {
    // Intercept fetch requests
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      
      // Check for 401 Unauthorized
      if (response.status === 401) {
        console.warn('Auth required: 401 response detected');
        
        if (options.onAuthRequired) {
          options.onAuthRequired();
        } else {
          // Default: show alert and redirect to login
          alert('Your session has expired. Please log in again.');
          navigate('/login');
        }
      }
      
      return response;
    };
    
    // Cleanup on unmount
    return () => {
      window.fetch = originalFetch;
    };
  }, [navigate, options]);
};

export default useAuthInterceptor;

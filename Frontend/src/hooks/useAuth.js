import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      setUser({ token });
    }
    setLoading(false);
  }, []);

  const signIn = async (credentials) => {
    setError(null);
    try {
      const response = await authAPI.signIn(credentials);
      const token = response.access_token;
      if (!token) {
        throw new Error('Missing access token');
      }
      localStorage.setItem('authToken', token);
      setUser({ token });
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const sendOTP = async (data) => {
    setError(null);
    try {
      const response = await authAPI.signUp(data);
      return { success: true, message: response.message };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const verifyOTP = async (data) => {
    setError(null);
    try {
      const response = await authAPI.verifyOTP(data);
      return { success: true, message: response.message };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const signOut = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return {
    user,
    loading,
    error,
    signIn,
    sendOTP,
    verifyOTP,
    signOut,
    isAuthenticated: !!user,
  };
};

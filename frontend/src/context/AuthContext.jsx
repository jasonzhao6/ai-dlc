import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [username, setUsername] = useState(localStorage.getItem('username'));
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [forcePasswordChange, setForcePasswordChange] = useState(
    localStorage.getItem('forcePasswordChange') === 'true'
  );

  const login = (data) => {
    localStorage.setItem('token', data.token);
    localStorage.setItem('username', data.username);
    localStorage.setItem('role', data.role);
    localStorage.setItem('forcePasswordChange', data.force_password_change ? 'true' : 'false');
    setToken(data.token);
    setUsername(data.username);
    setRole(data.role);
    setForcePasswordChange(data.force_password_change || false);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore logout errors
    }
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('forcePasswordChange');
    setToken(null);
    setUsername(null);
    setRole(null);
    setForcePasswordChange(false);
  };

  const clearForcePasswordChange = () => {
    localStorage.setItem('forcePasswordChange', 'false');
    setForcePasswordChange(false);
  };

  const isAuthenticated = !!token;
  const isAdmin = role === 'Admin';

  return (
    <AuthContext.Provider value={{
      token, username, role, isAuthenticated, isAdmin,
      forcePasswordChange, login, logout, clearForcePasswordChange
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

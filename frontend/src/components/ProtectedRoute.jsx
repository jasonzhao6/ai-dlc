import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin, forcePasswordChange } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (forcePasswordChange) {
    return <Navigate to="/change-password" replace />;
  }

  if (adminOnly && !isAdmin) {
    return (
      <div className="text-center mt-5">
        <i className="bi bi-shield-lock text-danger" style={{ fontSize: '3rem' }}></i>
        <h3 className="mt-3">Access Denied</h3>
        <p className="text-muted">You don't have permission to view this page.</p>
      </div>
    );
  }

  return children;
}

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';

export default function SettingsPage() {
  const { username, role } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h4 className="mb-4">
        <i className="bi bi-gear me-2"></i>Settings
      </h4>

      <div className="row">
        <div className="col-lg-6">
          {/* Account Info */}
          <div className="card mb-4">
            <div className="card-header bg-fs-light">
              <h6 className="mb-0"><i className="bi bi-person-circle me-2"></i>Account Info</h6>
            </div>
            <div className="card-body">
              <div className="mb-2">
                <strong>Username:</strong> {username}
              </div>
              <div>
                <strong>Role:</strong>{' '}
                <span className={`badge badge-${role?.toLowerCase()}`}>{role}</span>
              </div>
            </div>
          </div>

          {/* Change Password */}
          <div className="card">
            <div className="card-header bg-fs-light">
              <h6 className="mb-0"><i className="bi bi-lock me-2"></i>Change Password</h6>
            </div>
            <div className="card-body">
              {error && (
                <div className="alert alert-danger py-2 d-flex align-items-center">
                  <i className="bi bi-exclamation-circle me-2"></i>{error}
                </div>
              )}
              {success && (
                <div className="alert alert-success py-2 d-flex align-items-center">
                  <i className="bi bi-check-circle me-2"></i>{success}
                </div>
              )}
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="currentPw" className="form-label">Current Password</label>
                  <input
                    type="password"
                    id="currentPw"
                    className="form-control"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="newPw" className="form-label">New Password</label>
                  <input
                    type="password"
                    id="newPw"
                    className="form-control"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                  <div className="form-text">At least 8 characters</div>
                </div>
                <div className="mb-3">
                  <label htmlFor="confirmPw" className="form-label">Confirm New Password</label>
                  <input
                    type="password"
                    id="confirmPw"
                    className="form-control"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      Saving...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-check-lg me-2"></i>
                      Update Password
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

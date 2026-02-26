import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import ErrorBanner from '../components/ErrorBanner';

export default function AdminUserListPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Create user modal state
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ username: '', password: '', role: 'Viewer' });
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  // Edit user modal state
  const [editUser, setEditUser] = useState(null);
  const [editForm, setEditForm] = useState({ role: '', status: '' });
  const [editError, setEditError] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Reset password
  const [resetResult, setResetResult] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (roleFilter) params.role = roleFilter;
      if (statusFilter) params.status = statusFilter;
      const { data } = await api.get('/users', { params });
      setUsers(data.users || []);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter, statusFilter]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      await api.post('/users', createForm);
      setShowCreate(false);
      setCreateForm({ username: '', password: '', role: 'Viewer' });
      fetchUsers();
    } catch (err) {
      setCreateError(err.response?.data?.error || 'Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    setEditError('');
    setSaving(true);
    try {
      const updates = {};
      if (editForm.role && editForm.role !== editUser.role) updates.role = editForm.role;
      if (editForm.status && editForm.status !== editUser.status) updates.status = editForm.status;
      if (Object.keys(updates).length === 0) {
        setEditUser(null);
        return;
      }
      await api.put(`/users/${editUser.username}`, updates);
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      setEditError(err.response?.data?.error || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/users/${deleteTarget}`);
      setDeleteTarget(null);
      fetchUsers();
    } catch (err) {
      setError(err);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const handleResetPassword = async (username) => {
    try {
      const { data } = await api.post(`/users/${username}/reset-password`);
      setResetResult({ username, password: data.temporary_password });
    } catch (err) {
      setError(err);
    }
  };

  const openEdit = (user) => {
    setEditUser(user);
    setEditForm({ role: user.role, status: user.status });
    setEditError('');
  };

  const formatDate = (ts) => {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleDateString();
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="mb-0">
          <i className="bi bi-people me-2"></i>User Management
        </h4>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <i className="bi bi-person-plus me-1"></i>Create User
        </button>
      </div>

      <ErrorBanner error={error} onRetry={fetchUsers} onDismiss={() => setError(null)} />

      {/* Filters */}
      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="row g-2 align-items-center">
            <div className="col-auto">
              <label className="col-form-label small text-muted">Filter:</label>
            </div>
            <div className="col-auto">
              <select
                className="form-select form-select-sm"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <option value="">All Roles</option>
                <option value="Admin">Admin</option>
                <option value="Uploader">Uploader</option>
                <option value="Reader">Reader</option>
                <option value="Viewer">Viewer</option>
              </select>
            </div>
            <div className="col-auto">
              <select
                className="form-select form-select-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
            {(roleFilter || statusFilter) && (
              <div className="col-auto">
                <button
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => { setRoleFilter(''); setStatusFilter(''); }}
                >
                  <i className="bi bi-x-lg me-1"></i>Clear
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-fs-primary" role="status"></div>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table table-hover align-middle">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr><td colSpan="5" className="text-center text-muted py-4">No users found</td></tr>
              ) : (
                users.map((user) => (
                  <tr key={user.username}>
                    <td>
                      <i className="bi bi-person me-1"></i>
                      <strong>{user.username}</strong>
                    </td>
                    <td>
                      <span className={`badge badge-${user.role?.toLowerCase()}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${user.status === 'active' ? 'bg-success' : 'bg-secondary'}`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="text-muted small">{formatDate(user.created_at)}</td>
                    <td className="text-end">
                      <div className="btn-group btn-group-sm">
                        <button
                          className="btn btn-outline-primary"
                          onClick={() => openEdit(user)}
                          title="Edit"
                        >
                          <i className="bi bi-pencil"></i>
                        </button>
                        <button
                          className="btn btn-outline-warning"
                          onClick={() => handleResetPassword(user.username)}
                          title="Reset Password"
                        >
                          <i className="bi bi-key"></i>
                        </button>
                        <button
                          className="btn btn-outline-danger"
                          onClick={() => setDeleteTarget(user.username)}
                          title="Delete"
                        >
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreate && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title"><i className="bi bi-person-plus me-2"></i>Create User</h5>
                <button className="btn-close" onClick={() => setShowCreate(false)}></button>
              </div>
              <form onSubmit={handleCreateUser}>
                <div className="modal-body">
                  {createError && (
                    <div className="alert alert-danger py-2">{createError}</div>
                  )}
                  <div className="mb-3">
                    <label className="form-label">Username</label>
                    <input
                      type="text"
                      className="form-control"
                      value={createForm.username}
                      onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                      required
                      autoFocus
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Password</label>
                    <input
                      type="password"
                      className="form-control"
                      value={createForm.password}
                      onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                      required
                      minLength={8}
                    />
                    <div className="form-text">At least 8 characters. User will be required to change it on first login.</div>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Role</label>
                    <select
                      className="form-select"
                      value={createForm.role}
                      onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                    >
                      <option value="Admin">Admin</option>
                      <option value="Uploader">Uploader</option>
                      <option value="Reader">Reader</option>
                      <option value="Viewer">Viewer</option>
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={creating}>
                    {creating ? 'Creating...' : 'Create User'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editUser && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-pencil me-2"></i>Edit User: {editUser.username}
                </h5>
                <button className="btn-close" onClick={() => setEditUser(null)}></button>
              </div>
              <form onSubmit={handleEditUser}>
                <div className="modal-body">
                  {editError && (
                    <div className="alert alert-danger py-2">{editError}</div>
                  )}
                  <div className="mb-3">
                    <label className="form-label">Role</label>
                    <select
                      className="form-select"
                      value={editForm.role}
                      onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                    >
                      <option value="Admin">Admin</option>
                      <option value="Uploader">Uploader</option>
                      <option value="Reader">Reader</option>
                      <option value="Viewer">Viewer</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Status</label>
                    <select
                      className="form-select"
                      value={editForm.status}
                      onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    >
                      <option value="active">Active</option>
                      <option value="disabled">Disabled</option>
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setEditUser(null)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title text-danger">
                  <i className="bi bi-exclamation-triangle me-2"></i>Delete User
                </h5>
                <button className="btn-close" onClick={() => setDeleteTarget(null)}></button>
              </div>
              <div className="modal-body">
                <p>Are you sure you want to delete user <strong>{deleteTarget}</strong>?</p>
                <p className="text-muted small mb-0">This will remove the user and all their sessions.</p>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button>
                <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Password Result Modal */}
      {resetResult && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-key me-2"></i>Password Reset
                </h5>
                <button className="btn-close" onClick={() => setResetResult(null)}></button>
              </div>
              <div className="modal-body">
                <p>Temporary password for <strong>{resetResult.username}</strong>:</p>
                <div className="bg-light p-2 rounded font-monospace text-center">
                  {resetResult.password}
                </div>
                <p className="text-muted small mt-2 mb-0">
                  The user will be required to change this password on next login.
                </p>
              </div>
              <div className="modal-footer">
                <button className="btn btn-primary" onClick={() => setResetResult(null)}>Done</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

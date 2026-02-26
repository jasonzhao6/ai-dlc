import { useState, useEffect } from 'react';
import api from '../api/client';
import ErrorBanner from '../components/ErrorBanner';

export default function AdminFolderPage() {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Create folder
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', parent_id: 'ROOT' });
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  // Rename folder
  const [renameFolder, setRenameFolder] = useState(null);
  const [renameName, setRenameName] = useState('');
  const [renameError, setRenameError] = useState('');
  const [renaming, setRenaming] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Assignments
  const [assignFolder, setAssignFolder] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [assignUsername, setAssignUsername] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);

  const fetchFolders = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/folders');
      setFolders(data.folders || []);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFolders(); }, []);

  const flattenFolders = (tree, depth = 0) => {
    const result = [];
    for (const f of tree) {
      result.push({ ...f, depth });
      if (f.children) {
        result.push(...flattenFolders(f.children, depth + 1));
      }
    }
    return result;
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      await api.post('/folders', createForm);
      setShowCreate(false);
      setCreateForm({ name: '', parent_id: 'ROOT' });
      fetchFolders();
    } catch (err) {
      setCreateError(err.response?.data?.error || 'Failed to create folder');
    } finally {
      setCreating(false);
    }
  };

  const handleRename = async (e) => {
    e.preventDefault();
    setRenameError('');
    setRenaming(true);
    try {
      await api.put(`/folders/${renameFolder.folder_id}`, { name: renameName });
      setRenameFolder(null);
      fetchFolders();
    } catch (err) {
      setRenameError(err.response?.data?.error || 'Failed to rename folder');
    } finally {
      setRenaming(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/folders/${deleteTarget.folder_id}`);
      setDeleteTarget(null);
      fetchFolders();
    } catch (err) {
      setError(err);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const openAssignments = async (folder) => {
    setAssignFolder(folder);
    setAssignLoading(true);
    try {
      const [assignRes, usersRes] = await Promise.all([
        api.get(`/folders/${folder.folder_id}/assignments`),
        api.get('/users'),
      ]);
      setAssignments(assignRes.data.assignments || []);
      setAllUsers(usersRes.data.users || []);
    } catch (err) {
      setError(err);
    } finally {
      setAssignLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!assignUsername) return;
    try {
      await api.post(`/folders/${assignFolder.folder_id}/assignments`, {
        usernames: [assignUsername],
      });
      setAssignUsername('');
      // Refresh assignments
      const { data } = await api.get(`/folders/${assignFolder.folder_id}/assignments`);
      setAssignments(data.assignments || []);
    } catch (err) {
      setError(err);
    }
  };

  const handleUnassign = async (username) => {
    try {
      await api.delete(`/folders/${assignFolder.folder_id}/assignments/${username}`);
      setAssignments(assignments.filter((a) => a.username !== username));
    } catch (err) {
      setError(err);
    }
  };

  const flat = flattenFolders(folders);
  const assignedUsernames = new Set(assignments.map((a) => a.username));
  const unassignedUsers = allUsers.filter((u) => !assignedUsernames.has(u.username));

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="mb-0">
          <i className="bi bi-folder-plus me-2"></i>Folder Management
        </h4>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <i className="bi bi-plus-lg me-1"></i>Create Folder
        </button>
      </div>

      <ErrorBanner error={error} onRetry={fetchFolders} onDismiss={() => setError(null)} />

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-fs-primary" role="status"></div>
        </div>
      ) : flat.length === 0 ? (
        <div className="text-center text-muted py-5">
          <i className="bi bi-folder2-open" style={{ fontSize: '3rem' }}></i>
          <p className="mt-2">No folders yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table table-hover align-middle">
            <thead>
              <tr>
                <th>Folder</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {flat.map((f) => (
                <tr key={f.folder_id}>
                  <td>
                    <span style={{ paddingLeft: `${f.depth * 1.5}rem` }}>
                      <i className={`bi ${f.depth === 0 ? 'bi-folder-fill text-fs-primary' : 'bi-folder text-muted'} me-2`}></i>
                      {f.name}
                    </span>
                  </td>
                  <td className="text-end">
                    <div className="btn-group btn-group-sm">
                      <button
                        className="btn btn-outline-primary"
                        title="Rename"
                        onClick={() => { setRenameFolder(f); setRenameName(f.name); setRenameError(''); }}
                      >
                        <i className="bi bi-pencil"></i>
                      </button>
                      <button
                        className="btn btn-outline-info"
                        title="Assignments"
                        onClick={() => openAssignments(f)}
                      >
                        <i className="bi bi-people"></i>
                      </button>
                      <button
                        className="btn btn-outline-danger"
                        title="Delete"
                        onClick={() => setDeleteTarget(f)}
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Folder Modal */}
      {showCreate && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title"><i className="bi bi-folder-plus me-2"></i>Create Folder</h5>
                <button className="btn-close" onClick={() => setShowCreate(false)}></button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="modal-body">
                  {createError && <div className="alert alert-danger py-2">{createError}</div>}
                  <div className="mb-3">
                    <label className="form-label">Folder Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={createForm.name}
                      onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                      required
                      autoFocus
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Parent Folder</label>
                    <select
                      className="form-select"
                      value={createForm.parent_id}
                      onChange={(e) => setCreateForm({ ...createForm, parent_id: e.target.value })}
                    >
                      <option value="ROOT">Root (top-level)</option>
                      {flat.map((f) => (
                        <option key={f.folder_id} value={f.folder_id}>
                          {'  '.repeat(f.depth)}{f.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={creating}>
                    {creating ? 'Creating...' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {renameFolder && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Rename Folder</h5>
                <button className="btn-close" onClick={() => setRenameFolder(null)}></button>
              </div>
              <form onSubmit={handleRename}>
                <div className="modal-body">
                  {renameError && <div className="alert alert-danger py-2">{renameError}</div>}
                  <input
                    type="text"
                    className="form-control"
                    value={renameName}
                    onChange={(e) => setRenameName(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setRenameFolder(null)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={renaming}>
                    {renaming ? 'Saving...' : 'Rename'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title text-danger">
                  <i className="bi bi-exclamation-triangle me-2"></i>Delete Folder
                </h5>
                <button className="btn-close" onClick={() => setDeleteTarget(null)}></button>
              </div>
              <div className="modal-body">
                <p>Delete <strong>{deleteTarget.name}</strong>?</p>
                <p className="text-muted small mb-0">
                  This will also delete all sub-folders, files, and assignments.
                </p>
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

      {/* Assignments Modal */}
      {assignFolder && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-people me-2"></i>Assignments: {assignFolder.name}
                </h5>
                <button className="btn-close" onClick={() => setAssignFolder(null)}></button>
              </div>
              <div className="modal-body">
                {assignLoading ? (
                  <div className="text-center py-3">
                    <div className="spinner-border spinner-border-sm" role="status"></div>
                  </div>
                ) : (
                  <>
                    {/* Add assignment */}
                    <div className="input-group mb-3">
                      <select
                        className="form-select"
                        value={assignUsername}
                        onChange={(e) => setAssignUsername(e.target.value)}
                      >
                        <option value="">Select user to assign...</option>
                        {unassignedUsers.map((u) => (
                          <option key={u.username} value={u.username}>
                            {u.username} ({u.role})
                          </option>
                        ))}
                      </select>
                      <button
                        className="btn btn-primary"
                        onClick={handleAssign}
                        disabled={!assignUsername}
                      >
                        <i className="bi bi-plus-lg"></i>
                      </button>
                    </div>

                    {/* Current assignments */}
                    {assignments.length === 0 ? (
                      <p className="text-muted text-center">No users assigned</p>
                    ) : (
                      <ul className="list-group">
                        {assignments.map((a) => (
                          <li key={a.username} className="list-group-item d-flex justify-content-between align-items-center">
                            <span>
                              <i className="bi bi-person me-2"></i>{a.username}
                            </span>
                            <button
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => handleUnassign(a.username)}
                            >
                              <i className="bi bi-x-lg"></i>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setAssignFolder(null)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

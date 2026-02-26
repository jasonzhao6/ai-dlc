import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import ErrorBanner from '../components/ErrorBanner';

export default function FolderBrowserPage() {
  const { folderId } = useParams();
  const navigate = useNavigate();
  const { username, role } = useAuth();
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentFolder, setCurrentFolder] = useState(null);
  const [breadcrumbs, setBreadcrumbs] = useState([]);

  // Upload state
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFileName, setUploadFileName] = useState('');

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Sort state
  const [sortField, setSortField] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  const canUpload = role === 'Admin' || role === 'Uploader';
  const canDownload = role === 'Admin' || role === 'Reader';

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/folders');
      setFolders(data.folders || []);

      if (folderId) {
        const found = findFolder(data.folders || [], folderId);
        setCurrentFolder(found);
        setBreadcrumbs(found ? buildBreadcrumbs(data.folders || [], folderId) : []);

        // Fetch files for this folder
        const filesRes = await api.get(`/folders/${folderId}/files`);
        setFiles(filesRes.data.files || []);
      } else {
        setCurrentFolder(null);
        setBreadcrumbs([]);
        setFiles([]);
      }
    } catch (err) {
      if (err.response?.status !== 403) {
        setError(err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [folderId]);

  const findFolder = (tree, targetId) => {
    for (const f of tree) {
      if (f.folder_id === targetId) return f;
      if (f.children) {
        const found = findFolder(f.children, targetId);
        if (found) return found;
      }
    }
    return null;
  };

  const buildBreadcrumbs = (tree, targetId) => {
    const path = [];
    const search = (nodes, trail) => {
      for (const f of nodes) {
        const current = [...trail, { folder_id: f.folder_id, name: f.name }];
        if (f.folder_id === targetId) { path.push(...current); return true; }
        if (f.children && search(f.children, current)) return true;
      }
      return false;
    };
    search(tree, []);
    return path;
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const MAX_SIZE = 1 * 1024 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setError({ response: { data: { error: 'File size exceeds 1 GB limit' } } });
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadFileName(file.name);

    try {
      // 1. Get pre-signed URL
      const { data: urlData } = await api.post('/files/upload-url', {
        folder_id: folderId,
        file_name: file.name,
        file_size: file.size,
      });

      // 2. Upload to S3 via pre-signed URL with progress
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener('progress', (evt) => {
          if (evt.lengthComputable) {
            setUploadProgress(Math.round((evt.loaded / evt.total) * 100));
          }
        });
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) resolve();
          else reject(new Error(`Upload failed: ${xhr.status}`));
        });
        xhr.addEventListener('error', () => reject(new Error('Upload failed')));
        xhr.open('PUT', urlData.upload_url);
        xhr.setRequestHeader('Content-Type', 'application/octet-stream');
        xhr.send(file);
      });

      // 3. Confirm upload
      await api.post('/files/confirm-upload', {
        file_id: urlData.file_id,
        folder_id: folderId,
        file_name: file.name,
        file_size: file.size,
        s3_key: urlData.s3_key,
      });

      fetchData();
    } catch (err) {
      setError(err);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setUploadFileName('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDownload = async (file) => {
    try {
      const { data } = await api.post('/files/download-url', {
        file_id: file.file_id,
        folder_id: file.folder_id,
      });
      window.open(data.download_url, '_blank');
    } catch (err) {
      setError(err);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/files/${deleteTarget.file_id}?folder_id=${deleteTarget.folder_id}`);
      setDeleteTarget(null);
      fetchData();
    } catch (err) {
      setError(err);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const canDeleteFile = (file) => {
    return role === 'Admin' || (role === 'Uploader' && file.uploaded_by === username);
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sortedFiles = [...files].sort((a, b) => {
    let valA, valB;
    switch (sortField) {
      case 'name': valA = a.name?.toLowerCase() || ''; valB = b.name?.toLowerCase() || ''; break;
      case 'size': valA = a.size || 0; valB = b.size || 0; break;
      case 'uploaded_at': valA = a.uploaded_at || 0; valB = b.uploaded_at || 0; break;
      default: valA = ''; valB = '';
    }
    if (valA < valB) return sortDir === 'asc' ? -1 : 1;
    if (valA > valB) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <i className="bi bi-arrow-down-up ms-1 opacity-25"></i>;
    return sortDir === 'asc'
      ? <i className="bi bi-arrow-up ms-1"></i>
      : <i className="bi bi-arrow-down ms-1"></i>;
  };

  const formatSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const formatDate = (ts) => {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleString();
  };

  const displayFolders = folderId && currentFolder
    ? currentFolder.children || []
    : folders;

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-fs-primary" role="status"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <nav aria-label="breadcrumb" className="mb-3">
          <ol className="breadcrumb">
            <li className="breadcrumb-item">
              <Link to="/folders"><i className="bi bi-house me-1"></i>Root</Link>
            </li>
            {breadcrumbs.map((bc, i) => (
              <li key={bc.folder_id} className={`breadcrumb-item ${i === breadcrumbs.length - 1 ? 'active' : ''}`}>
                {i === breadcrumbs.length - 1 ? bc.name : (
                  <Link to={`/folders/${bc.folder_id}`}>{bc.name}</Link>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="mb-0">
          <i className="bi bi-folder2 me-2"></i>
          {currentFolder ? currentFolder.name : 'Folders'}
        </h4>
        <div>
          {folderId && canUpload && (
            <>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleUpload}
                className="d-none"
              />
              <button
                className="btn btn-primary me-2"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <i className="bi bi-cloud-arrow-up me-1"></i>Upload
              </button>
            </>
          )}
          {folderId && (
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => {
                const parentId = currentFolder?.parent_id;
                navigate(parentId && parentId !== 'ROOT' ? `/folders/${parentId}` : '/folders');
              }}
            >
              <i className="bi bi-arrow-left me-1"></i>Back
            </button>
          )}
        </div>
      </div>

      <ErrorBanner error={error} onRetry={fetchData} onDismiss={() => setError(null)} />

      {/* Upload Progress */}
      {uploading && (
        <div className="alert alert-info py-2 d-flex align-items-center">
          <div className="flex-grow-1">
            <div className="d-flex justify-content-between mb-1">
              <small>Uploading {uploadFileName}...</small>
              <small>{uploadProgress}%</small>
            </div>
            <div className="progress" style={{ height: '8px' }}>
              <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
            </div>
          </div>
        </div>
      )}

      {/* Sub-folders */}
      {displayFolders.length > 0 && (
        <div className="row g-3 mb-4">
          {displayFolders.map((folder) => (
            <div key={folder.folder_id} className="col-sm-6 col-md-4 col-lg-3">
              <div className="card h-100" style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/folders/${folder.folder_id}`)}>
                <div className="card-body text-center py-4">
                  <i className="bi bi-folder-fill text-fs-primary" style={{ fontSize: '2.5rem' }}></i>
                  <h6 className="mt-2 mb-1">{folder.name}</h6>
                  {folder.children?.length > 0 && (
                    <small className="text-muted">
                      {folder.children.length} sub-folder{folder.children.length !== 1 ? 's' : ''}
                    </small>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Files table */}
      {folderId && (
        <>
          <h5 className="mb-3"><i className="bi bi-file-earmark me-2"></i>Files</h5>
          {files.length === 0 ? (
            <div className="text-center text-muted py-4 border rounded">
              <i className="bi bi-file-earmark-plus" style={{ fontSize: '2rem' }}></i>
              <p className="mt-1 mb-0">No files in this folder</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead>
                  <tr>
                    <th className="sortable-header" onClick={() => handleSort('name')}>
                      Name <SortIcon field="name" />
                    </th>
                    <th className="sortable-header" onClick={() => handleSort('size')}>
                      Size <SortIcon field="size" />
                    </th>
                    <th>Uploaded By</th>
                    <th className="sortable-header" onClick={() => handleSort('uploaded_at')}>
                      Date <SortIcon field="uploaded_at" />
                    </th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFiles.map((file) => (
                    <tr key={file.file_id}>
                      <td>
                        <i className="bi bi-file-earmark me-2 text-muted"></i>
                        {file.name}
                      </td>
                      <td className="text-muted">{formatSize(file.size)}</td>
                      <td className="text-muted">{file.uploaded_by}</td>
                      <td className="text-muted small">{formatDate(file.uploaded_at)}</td>
                      <td className="text-end">
                        <div className="btn-group btn-group-sm">
                          {canDownload && (
                            <button
                              className="btn btn-outline-primary"
                              onClick={() => handleDownload(file)}
                              title="Download"
                            >
                              <i className="bi bi-download"></i>
                            </button>
                          )}
                          {canDeleteFile(file) && (
                            <button
                              className="btn btn-outline-danger"
                              onClick={() => setDeleteTarget(file)}
                              title="Delete"
                            >
                              <i className="bi bi-trash"></i>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* No folders and not viewing a folder */}
      {!folderId && displayFolders.length === 0 && (
        <div className="text-center text-muted py-5">
          <i className="bi bi-folder2-open" style={{ fontSize: '3rem' }}></i>
          <p className="mt-2">No folders available</p>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title text-danger">
                  <i className="bi bi-exclamation-triangle me-2"></i>Delete File
                </h5>
                <button className="btn-close" onClick={() => setDeleteTarget(null)}></button>
              </div>
              <div className="modal-body">
                <p>Delete <strong>{deleteTarget.name}</strong>?</p>
                <p className="text-muted small mb-0">This cannot be undone.</p>
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
    </div>
  );
}

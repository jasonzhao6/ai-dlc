import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import ErrorBanner from '../components/ErrorBanner';

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const { username, role } = useAuth();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  const canDownload = role === 'Admin' || role === 'Reader';

  useEffect(() => {
    if (!query) return;
    const search = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get(`/files/search?q=${encodeURIComponent(query)}`);
        setFiles(data.files || []);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };
    search();
  }, [query]);

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

  const formatDate = (ts) => ts ? new Date(ts * 1000).toLocaleString() : '—';

  const handleDownload = async (file) => {
    try {
      const { data } = await api.post('/files/download-url', {
        file_id: file.file_id, folder_id: file.folder_id,
      });
      window.open(data.download_url, '_blank');
    } catch (err) {
      setError(err);
    }
  };

  if (!query) {
    return (
      <div className="text-center text-muted py-5">
        <i className="bi bi-search" style={{ fontSize: '3rem' }}></i>
        <p className="mt-2">Enter a search query to find files</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="mb-4">
        <i className="bi bi-search me-2"></i>
        Search results for "{query}"
      </h4>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-fs-primary" role="status"></div>
        </div>
      ) : sortedFiles.length === 0 ? (
        <div className="text-center text-muted py-5">
          <i className="bi bi-file-earmark-x" style={{ fontSize: '3rem' }}></i>
          <p className="mt-2">No files found matching "{query}"</p>
        </div>
      ) : (
        <>
          <p className="text-muted mb-3">{sortedFiles.length} result{sortedFiles.length !== 1 ? 's' : ''}</p>
          <div className="table-responsive">
            <table className="table table-hover align-middle">
              <thead>
                <tr>
                  <th className="sortable-header" onClick={() => handleSort('name')}>
                    Name <SortIcon field="name" />
                  </th>
                  <th>Folder</th>
                  <th className="sortable-header" onClick={() => handleSort('size')}>
                    Size <SortIcon field="size" />
                  </th>
                  <th>Uploaded By</th>
                  <th className="sortable-header" onClick={() => handleSort('uploaded_at')}>
                    Date <SortIcon field="uploaded_at" />
                  </th>
                  {canDownload && <th className="text-end">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {sortedFiles.map((file) => (
                  <tr key={file.file_id}>
                    <td>
                      <i className="bi bi-file-earmark me-2 text-muted"></i>
                      {file.name}
                    </td>
                    <td>
                      <Link to={`/folders/${file.folder_id}`} className="text-decoration-none">
                        <small className="text-muted">{file.folder_path}</small>
                      </Link>
                    </td>
                    <td className="text-muted">{formatSize(file.size)}</td>
                    <td className="text-muted">{file.uploaded_by}</td>
                    <td className="text-muted small">{formatDate(file.uploaded_at)}</td>
                    {canDownload && (
                      <td className="text-end">
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => handleDownload(file)}
                          title="Download"
                        >
                          <i className="bi bi-download"></i>
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

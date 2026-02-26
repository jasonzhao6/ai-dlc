import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { username, role, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (q) {
      navigate(`/search?q=${encodeURIComponent(q)}`);
    }
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg navbar-fs px-3">
        <a className="navbar-brand fw-bold" href="/">
          <i className="bi bi-cloud-arrow-up-fill me-2"></i>FileShare
        </a>
        <form className="d-flex mx-auto" onSubmit={handleSearch} style={{ maxWidth: '400px', flex: 1 }}>
          <div className="input-group input-group-sm">
            <input
              type="text"
              className="form-control"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button className="btn btn-outline-light" type="submit">
              <i className="bi bi-search"></i>
            </button>
          </div>
        </form>
        <div className="ms-auto d-flex align-items-center">
          <span className="text-light me-3 small">
            <i className="bi bi-person-circle me-1"></i>
            {username}
            <span className={`badge ms-2 badge-${role?.toLowerCase()}`}>{role}</span>
          </span>
          <button className="btn btn-sm btn-outline-light" onClick={handleLogout}>
            <i className="bi bi-box-arrow-right me-1"></i>Logout
          </button>
        </div>
      </nav>

      <div className="d-flex flex-grow-1">
        {/* Sidebar */}
        <nav className="sidebar-fs d-none d-md-block" style={{ width: '240px' }}>
          <div className="p-3">
            <div className="nav flex-column">
              <NavLink to="/folders" className="nav-link">
                <i className="bi bi-folder2 me-2"></i>Folders
              </NavLink>
              {role === 'Admin' && (
                <>
                  <hr className="my-2" />
                  <small className="text-muted px-3 mb-1">Admin</small>
                  <NavLink to="/admin/users" className="nav-link">
                    <i className="bi bi-people me-2"></i>Users
                  </NavLink>
                  <NavLink to="/admin/folders" className="nav-link">
                    <i className="bi bi-folder-plus me-2"></i>Manage Folders
                  </NavLink>
                </>
              )}
              <hr className="my-2" />
              <NavLink to="/settings" className="nav-link">
                <i className="bi bi-gear me-2"></i>Settings
              </NavLink>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-grow-1 p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

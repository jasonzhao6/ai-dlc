import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import SettingsPage from './pages/SettingsPage';
import FolderBrowserPage from './pages/FolderBrowserPage';
import AdminUserListPage from './pages/AdminUserListPage';
import AdminFolderPage from './pages/AdminFolderPage';
import SearchResultsPage from './pages/SearchResultsPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/change-password" element={<ChangePasswordPage />} />

          <Route path="/" element={
            <ProtectedRoute><Layout /></ProtectedRoute>
          }>
            <Route index element={<Navigate to="/folders" replace />} />
            <Route path="folders" element={<FolderBrowserPage />} />
            <Route path="folders/:folderId" element={<FolderBrowserPage />} />
            <Route path="search" element={<SearchResultsPage />} />
            <Route path="settings" element={<SettingsPage />} />

            {/* Admin routes */}
            <Route path="admin/users" element={
              <ProtectedRoute adminOnly><AdminUserListPage /></ProtectedRoute>
            } />
            <Route path="admin/folders" element={
              <ProtectedRoute adminOnly><AdminFolderPage /></ProtectedRoute>
            } />
          </Route>

          <Route path="*" element={<Navigate to="/folders" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

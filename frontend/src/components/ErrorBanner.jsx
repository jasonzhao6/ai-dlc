import { useState } from 'react';

export default function ErrorBanner({ error, onRetry, onDismiss }) {
  if (!error) return null;

  const isNetworkError = !error.response;
  const message = error.response?.data?.error
    || error.message
    || 'Something went wrong';

  return (
    <div className="alert alert-danger alert-dismissible fade show d-flex align-items-center" role="alert">
      <i className="bi bi-exclamation-triangle-fill me-2"></i>
      <div className="flex-grow-1">
        {isNetworkError ? 'Connection lost. Please check your network.' : message}
      </div>
      {(isNetworkError || error.response?.status >= 500) && onRetry && (
        <button className="btn btn-sm btn-outline-danger me-2" onClick={onRetry}>
          <i className="bi bi-arrow-clockwise me-1"></i>Retry
        </button>
      )}
      {onDismiss && (
        <button type="button" className="btn-close" onClick={onDismiss}></button>
      )}
    </div>
  );
}

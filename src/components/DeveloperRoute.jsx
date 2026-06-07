import './admin/AdminUserDashboard.css';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const DEV_EMAILS = (import.meta.env.VITE_DEVELOPER_EMAILS || 'kavi.cf412@gmail.com')
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

/**
 * Restricts routes to localhost + developer accounts only.
 */
const DeveloperRoute = ({ children }) => {
  const { currentUser, isDeveloper, hasCheckedDeveloperStatus } = useAuth();
  const isLocalhost =
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

  const emailIsDeveloper =
    currentUser?.email && DEV_EMAILS.includes(currentUser.email.toLowerCase());
  const canAccess = isDeveloper || emailIsDeveloper;

  if (!isLocalhost) {
    return <Navigate to="/" replace />;
  }

  // Wait only until Firebase auth resolves — don't block on slow subscription API.
  if (!hasCheckedDeveloperStatus && !currentUser) {
    return (
      <div className="admin-dash-loading">
        <div className="admin-dash-spinner" />
        <p>Checking developer access…</p>
      </div>
    );
  }

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccess && hasCheckedDeveloperStatus) {
    return (
      <div className="admin-dash-blocked">
        <h1>Access denied</h1>
        <p>This dashboard is only available to developer accounts on localhost.</p>
        <a href="/dashboard">Back to dashboard</a>
      </div>
    );
  }

  if (!canAccess) {
    return (
      <div className="admin-dash-loading">
        <div className="admin-dash-spinner" />
        <p>Verifying developer access…</p>
      </div>
    );
  }

  return children;
};

export default DeveloperRoute;

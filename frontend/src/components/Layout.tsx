/**
 * Main layout component with navigation.
 */
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  The Good Shepherd
                </h1>
              </Link>

              <div className="hidden md:flex ml-10 space-x-8">
                <Link
                  to="/"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Stream
                </Link>
                <Link
                  to="/map"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/map'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Map
                </Link>
                <Link
                  to="/dossiers"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/dossiers'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Dossiers
                </Link>
                <Link
                  to="/dashboard"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/dashboard'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Dashboard
                </Link>

                {/* Admin Section */}
                <div className="border-l border-gray-300 pl-8 ml-2">
                  <span className="text-xs text-gray-500 font-medium uppercase">Admin</span>
                </div>
                <Link
                  to="/audit"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/audit'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Audit Log
                </Link>
                <Link
                  to="/settings"
                  className={`px-3 py-2 text-sm font-medium ${
                    location.pathname === '/settings'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Settings
                </Link>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {user && (
                <>
                  <span className="text-sm text-gray-700">
                    {user.full_name || user.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-gray-700 hover:text-gray-900 font-medium"
                  >
                    Logout
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            The Good Shepherd - OSINT Intelligence Platform for Missionaries in Europe
          </p>
          <p className="text-center text-xs text-gray-400 mt-1">
            Version 0.8.0 | Production Ready | Read-only intelligence gathering
          </p>
        </div>
      </footer>
    </div>
  );
}

/**
 * Main layout component with navigation.
 * Features glass-morphism navigation bar and dark tactical theme.
 */
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useState } from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = [
    { to: '/', label: 'Awareness', paths: ['/', '/awareness'] },
    { to: '/stream', label: 'Stream', paths: ['/stream'] },
    { to: '/map', label: 'Map', paths: ['/map'] },
    { to: '/dossiers', label: 'Dossiers', paths: ['/dossiers'] },
    { to: '/dashboard', label: 'Analytics', paths: ['/dashboard'] },
  ];

  const adminLinks = [
    { to: '/audit', label: 'Audit Log', paths: ['/audit'] },
    { to: '/settings', label: 'Settings', paths: ['/settings'] },
  ];

  const isActive = (paths: string[]) => paths.includes(location.pathname);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Gradient Background Overlay */}
      <div className="fixed inset-0 bg-gradient-tactical pointer-events-none" />

      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              {/* Logo */}
              <Link to="/" className="flex items-center group">
                <div className="flex items-center space-x-3">
                  {/* Icon */}
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-primary-500/30">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-lg font-bold text-white group-hover:text-primary-400 transition-colors">
                      The Good Shepherd
                    </h1>
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest -mt-0.5">
                      Intelligence Platform
                    </p>
                  </div>
                </div>
              </Link>

              {/* Desktop Navigation */}
              <div className="hidden md:flex ml-10 space-x-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`nav-link ${isActive(link.paths) ? 'active' : ''}`}
                  >
                    {link.label}
                  </Link>
                ))}

                {/* Admin Section Divider */}
                <div className="flex items-center px-3">
                  <div className="h-6 w-px bg-white/10" />
                </div>
                <span className="flex items-center text-[10px] text-gray-500 font-medium uppercase tracking-widest px-2">
                  Admin
                </span>

                {adminLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`nav-link ${isActive(link.paths) ? 'active' : ''}`}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>

            {/* Right Side */}
            <div className="flex items-center space-x-4">
              {/* Status Indicator */}
              <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-xs text-emerald-400 font-medium">System Online</span>
              </div>

              {user && (
                <>
                  <div className="hidden sm:flex flex-col items-end">
                    <span className="text-sm text-gray-200 font-medium">
                      {user.full_name || user.email}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      Administrator
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="btn-secondary text-sm"
                  >
                    Logout
                  </button>
                </>
              )}

              {/* Mobile menu button */}
              <button
                className="md:hidden p-2 text-gray-400 hover:text-white"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/5 bg-slate-900/95">
            <div className="px-4 py-3 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    ${isActive(link.paths)
                      ? 'bg-primary-500/10 text-primary-400'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                  {link.label}
                </Link>
              ))}
              <div className="border-t border-white/5 my-2 pt-2">
                <span className="px-3 text-[10px] text-gray-500 uppercase tracking-widest">Admin</span>
                {adminLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors
                      ${isActive(link.paths)
                        ? 'bg-primary-500/10 text-primary-400'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main content */}
      <main className="relative py-6 px-4 sm:px-6 lg:px-8 animate-fade-in">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative border-t border-white/5 mt-12 bg-slate-900/30">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-primary-500 to-cyan-400 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm text-gray-400">
                The Good Shepherd — OSINT Intelligence for Missionaries in Europe
              </p>
            </div>
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span>Version 1.0.0</span>
              <span className="text-gray-600">|</span>
              <span className="flex items-center">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mr-1.5" />
                All Systems Operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

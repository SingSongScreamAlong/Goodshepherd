import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';

// Lazy load pages for better performance
const App = lazy(() => import('./App'));
const MobileDashboard = lazy(() => import('./components/mobile/MobileDashboard'));
const CheckInPage = lazy(() => import('./components/mobile/CheckInPage'));
const AnalystDashboard = lazy(() => import('./pages/AnalystDashboard'));

// Loading spinner
const LoadingSpinner = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    background: '#1a1a2e',
    color: '#fff',
  }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '3px solid #333',
        borderTop: '3px solid #4ade80',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 16px',
      }} />
      <p>Loading Good Shepherd...</p>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  </div>
);

// Detect if mobile device
const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  ) || window.innerWidth < 768;
};

// Home route - redirects based on device
const HomeRedirect = () => {
  return isMobile() ? <Navigate to="/mobile" replace /> : <Navigate to="/dashboard" replace />;
};

function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Home - auto-detect device */}
            <Route path="/" element={<HomeRedirect />} />
            
            {/* Mobile Routes */}
            <Route path="/mobile" element={<MobileDashboard />} />
            <Route path="/checkin" element={<CheckInPage />} />
            
            {/* Analyst Routes */}
            <Route path="/analyst" element={<AnalystDashboard />} />
            
            {/* Main Dashboard (original App) */}
            <Route path="/dashboard" element={<App />} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default AppRouter;

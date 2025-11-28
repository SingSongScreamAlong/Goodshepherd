/**
 * Analyst Dashboard Page
 * Main page combining all analyst tools and visualizations
 */

import React, { useState } from 'react';
import { EventTimeline, AdvancedSearch, ReviewQueue, AnalyticsDashboard } from '../components/analyst';

/**
 * Tab navigation component
 */
function TabNav({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'timeline', label: '📅 Timeline', icon: '📅' },
    { id: 'search', label: '🔍 Search', icon: '🔍' },
    { id: 'review', label: '📋 Review Queue', icon: '📋' },
  ];

  return (
    <nav className="tab-nav">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}

/**
 * Main Analyst Dashboard Page
 */
export default function AnalystDashboardPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AnalyticsDashboard />;
      case 'timeline':
        return <EventTimeline />;
      case 'search':
        return <AdvancedSearch />;
      case 'review':
        return <ReviewQueue />;
      default:
        return <AnalyticsDashboard />;
    }
  };

  return (
    <div className="analyst-dashboard-page">
      <style>{`
        .analyst-dashboard-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
          color: white;
        }

        .page-title {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .page-title-icon {
          font-size: 1.75rem;
        }

        .header-actions {
          display: flex;
          gap: 12px;
        }

        .header-btn {
          padding: 8px 16px;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          color: white;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .header-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .tab-nav {
          display: flex;
          background: white;
          border-bottom: 1px solid #e5e7eb;
          padding: 0 16px;
        }

        .tab-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 16px 20px;
          background: none;
          border: none;
          border-bottom: 3px solid transparent;
          font-size: 0.9375rem;
          color: #6b7280;
          cursor: pointer;
          transition: all 0.2s;
        }

        .tab-btn:hover {
          color: #374151;
          background: #f9fafb;
        }

        .tab-btn.active {
          color: #1e3a5f;
          border-bottom-color: #1e3a5f;
          font-weight: 500;
        }

        .tab-icon {
          font-size: 1.125rem;
        }

        .tab-content {
          flex: 1;
          overflow: hidden;
        }

        @media (max-width: 768px) {
          .tab-label {
            display: none;
          }

          .tab-btn {
            padding: 12px 16px;
          }

          .tab-icon {
            font-size: 1.25rem;
          }

          .page-title span:not(.page-title-icon) {
            display: none;
          }
        }
      `}</style>

      <header className="page-header">
        <h1 className="page-title">
          <span className="page-title-icon">🛡️</span>
          <span>Good Shepherd Analyst Console</span>
        </h1>
        <div className="header-actions">
          <button className="header-btn">📤 Export Report</button>
          <button className="header-btn">⚙️ Settings</button>
        </div>
      </header>

      <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="tab-content">
        {renderContent()}
      </main>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { AlertTriangle, X, Bell, Shield, Info } from 'lucide-react';

/**
 * Toast notification for real-time alerts
 */
export function AlertToast({ alert, onDismiss, autoDismiss = 8000 }) {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (autoDismiss > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoDismiss);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, 300);
  };

  if (!isVisible) return null;

  const priorityConfig = getPriorityConfig(alert.priority);

  return (
    <div
      className={`
        max-w-sm w-full bg-white rounded-lg shadow-lg border-l-4 overflow-hidden
        transform transition-all duration-300 ease-out
        ${priorityConfig.borderColor}
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 ${priorityConfig.iconColor}`}>
            {priorityConfig.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <p className={`text-sm font-semibold ${priorityConfig.textColor}`}>
                {alert.rule_name || 'Alert'}
              </p>
              <span className={`
                text-xs px-2 py-0.5 rounded-full font-medium
                ${priorityConfig.badgeBg} ${priorityConfig.badgeText}
              `}>
                {alert.priority?.toUpperCase() || 'ALERT'}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-900 font-medium line-clamp-2">
              {alert.event_title || alert.title}
            </p>
            {alert.region && (
              <p className="mt-1 text-xs text-gray-500">
                Region: {alert.region}
              </p>
            )}
          </div>
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X size={16} className="text-gray-400" />
          </button>
        </div>
      </div>
      
      {/* Progress bar for auto-dismiss */}
      {autoDismiss > 0 && (
        <div className="h-1 bg-gray-100">
          <div
            className={`h-full ${priorityConfig.progressColor} transition-all ease-linear`}
            style={{
              width: '100%',
              animation: `shrink ${autoDismiss}ms linear forwards`,
            }}
          />
        </div>
      )}
      
      <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
}

/**
 * Container for managing multiple toast notifications
 */
export function AlertToastContainer({ alerts, onDismiss }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3">
      {alerts.map((alert, index) => (
        <AlertToast
          key={alert.id || index}
          alert={alert}
          onDismiss={() => onDismiss(alert.id || index)}
        />
      ))}
    </div>
  );
}

function getPriorityConfig(priority) {
  switch (priority?.toLowerCase()) {
    case 'critical':
      return {
        icon: <AlertTriangle size={20} />,
        borderColor: 'border-red-500',
        iconColor: 'text-red-500',
        textColor: 'text-red-700',
        badgeBg: 'bg-red-100',
        badgeText: 'text-red-700',
        progressColor: 'bg-red-500',
      };
    case 'high':
      return {
        icon: <Shield size={20} />,
        borderColor: 'border-orange-500',
        iconColor: 'text-orange-500',
        textColor: 'text-orange-700',
        badgeBg: 'bg-orange-100',
        badgeText: 'text-orange-700',
        progressColor: 'bg-orange-500',
      };
    case 'medium':
      return {
        icon: <Bell size={20} />,
        borderColor: 'border-yellow-500',
        iconColor: 'text-yellow-500',
        textColor: 'text-yellow-700',
        badgeBg: 'bg-yellow-100',
        badgeText: 'text-yellow-700',
        progressColor: 'bg-yellow-500',
      };
    case 'low':
    default:
      return {
        icon: <Info size={20} />,
        borderColor: 'border-blue-500',
        iconColor: 'text-blue-500',
        textColor: 'text-blue-700',
        badgeBg: 'bg-blue-100',
        badgeText: 'text-blue-700',
        progressColor: 'bg-blue-500',
      };
  }
}

export default AlertToast;

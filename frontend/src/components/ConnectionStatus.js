import React from 'react';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { ConnectionState } from '../hooks/useWebSocket';

/**
 * Connection status indicator component
 */
export default function ConnectionStatus({ 
  connectionState, 
  lastHeartbeat,
  onReconnect,
  className = '',
}) {
  const getStatusConfig = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return {
          icon: Wifi,
          color: 'text-green-500',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Connected',
          description: lastHeartbeat 
            ? `Last ping: ${formatTime(lastHeartbeat)}`
            : 'Real-time updates active',
        };
      case ConnectionState.CONNECTING:
        return {
          icon: RefreshCw,
          color: 'text-blue-500',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          label: 'Connecting',
          description: 'Establishing connection...',
          animate: true,
        };
      case ConnectionState.RECONNECTING:
        return {
          icon: RefreshCw,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          label: 'Reconnecting',
          description: 'Connection lost, retrying...',
          animate: true,
        };
      case ConnectionState.ERROR:
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Error',
          description: 'Connection failed',
          showReconnect: true,
        };
      case ConnectionState.DISCONNECTED:
      default:
        return {
          icon: WifiOff,
          color: 'text-gray-500',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          label: 'Offline',
          description: 'Not connected to server',
          showReconnect: true,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div 
      className={`
        flex items-center gap-2 px-3 py-2 rounded-lg border
        ${config.bgColor} ${config.borderColor} ${className}
      `}
    >
      <Icon 
        size={16} 
        className={`${config.color} ${config.animate ? 'animate-spin' : ''}`} 
      />
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${config.color}`}>
          {config.label}
        </div>
        <div className="text-xs text-gray-500 truncate">
          {config.description}
        </div>
      </div>
      {config.showReconnect && onReconnect && (
        <button
          onClick={onReconnect}
          className="p-1 rounded hover:bg-gray-200 transition-colors"
          title="Reconnect"
        >
          <RefreshCw size={14} className="text-gray-600" />
        </button>
      )}
    </div>
  );
}

function formatTime(date) {
  if (!date) return '';
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return date.toLocaleTimeString();
}

/**
 * DossierCard component - displays a dossier with statistics and actions.
 */
import { useState } from 'react';
import { Dossier } from '../types';
import { getDossierTypeLabel, getDossierTypeColor } from '../utils/dossierFormatting';
import { formatRelativeTime } from '../utils/formatting';

interface DossierCardProps {
  dossier: Dossier;
  onEdit?: (dossier: Dossier) => void;
  onDelete?: (dossier: Dossier) => void;
  onRefresh?: (dossier: Dossier) => void;
  onViewDetails?: (dossier: Dossier) => void;
}

export default function DossierCard({
  dossier,
  onEdit,
  onDelete,
  onRefresh,
  onViewDetails,
}: DossierCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded ${getDossierTypeColor(dossier.dossier_type)}`}>
              {getDossierTypeLabel(dossier.dossier_type)}
            </span>
            {dossier.location_name && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                </svg>
                {dossier.location_name}
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{dossier.name}</h3>
          {dossier.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{dossier.description}</p>
          )}
        </div>

        {/* Actions menu */}
        <div className="relative ml-2">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded hover:bg-gray-100"
          >
            <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
              {onViewDetails && (
                <button
                  onClick={() => {
                    onViewDetails(dossier);
                    setShowMenu(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  View Details
                </button>
              )}
              {onRefresh && (
                <button
                  onClick={() => {
                    onRefresh(dossier);
                    setShowMenu(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Refresh Stats
                </button>
              )}
              {onEdit && (
                <button
                  onClick={() => {
                    onEdit(dossier);
                    setShowMenu(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Edit
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => {
                    if (window.confirm(`Delete dossier "${dossier.name}"?`)) {
                      onDelete(dossier);
                    }
                    setShowMenu(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  Delete
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Aliases */}
      {dossier.aliases && dossier.aliases.length > 0 && (
        <div className="mb-3">
          <span className="text-xs text-gray-500 mr-2">Aliases:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {dossier.aliases.map((alias, idx) => (
              <span key={idx} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                {alias}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tags */}
      {dossier.tags && dossier.tags.length > 0 && (
        <div className="mb-3">
          <div className="flex flex-wrap gap-1">
            {dossier.tags.map((tag, idx) => (
              <span key={idx} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="border-t border-gray-200 pt-3 mt-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-gray-500">Total Events</p>
            <p className="text-lg font-semibold text-gray-900">{dossier.event_count}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Last Activity</p>
            <p className="text-sm text-gray-700">
              {dossier.last_event_timestamp
                ? formatRelativeTime(dossier.last_event_timestamp)
                : 'No events'}
            </p>
          </div>
        </div>
      </div>

      {/* Notes preview */}
      {dossier.notes && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-1">Notes:</p>
          <p className="text-sm text-gray-600 line-clamp-2">{dossier.notes}</p>
        </div>
      )}
    </div>
  );
}

/**
 * Event card component for displaying enriched intelligence events.
 */
import { useState } from 'react';
import { Event } from '../types';
import {
  formatRelativeTime,
  formatDate,
  getCategoryColor,
  getCategoryLabel,
  getSentimentColor,
  getSentimentLabel,
  getRelevanceLabel,
  getConfidenceLabel,
} from '../utils/formatting';

interface EventCardProps {
  event: Event;
}

export default function EventCard({ event }: EventCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`px-2 py-1 text-xs font-medium rounded ${getCategoryColor(
                  event.category
                )}`}
              >
                {getCategoryLabel(event.category)}
              </span>

              {event.sentiment && (
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${getSentimentColor(
                    event.sentiment
                  )}`}
                >
                  {getSentimentLabel(event.sentiment)}
                </span>
              )}
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {event.summary}
            </h3>

            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span title={formatDate(event.timestamp)}>
                {formatRelativeTime(event.timestamp)}
              </span>

              {event.location_name && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {event.location_name}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Scores */}
          <div className="flex flex-col items-end gap-1 ml-4">
            {event.relevance_score !== undefined && (
              <div className="text-xs">
                <span className="text-gray-500">Relevance:</span>{' '}
                <span className="font-medium">
                  {getRelevanceLabel(event.relevance_score)}
                </span>
              </div>
            )}
            {event.confidence_score !== undefined && (
              <div className="text-xs">
                <span className="text-gray-500">Confidence:</span>{' '}
                <span className="font-medium">
                  {getConfidenceLabel(event.confidence_score)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Entities */}
        {event.entity_list && (
          <div className="mb-3 space-y-2">
            {event.entity_list.locations && event.entity_list.locations.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-xs text-gray-500 mr-1">Locations:</span>
                {event.entity_list.locations.slice(0, 5).map((loc, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                  >
                    {loc}
                  </span>
                ))}
                {event.entity_list.locations.length > 5 && (
                  <span className="text-xs text-gray-400">
                    +{event.entity_list.locations.length - 5} more
                  </span>
                )}
              </div>
            )}

            {event.entity_list.organizations &&
              event.entity_list.organizations.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-gray-500 mr-1">Organizations:</span>
                  {event.entity_list.organizations.slice(0, 5).map((org, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs bg-purple-50 text-purple-700 rounded"
                    >
                      {org}
                    </span>
                  ))}
                  {event.entity_list.organizations.length > 5 && (
                    <span className="text-xs text-gray-400">
                      +{event.entity_list.organizations.length - 5} more
                    </span>
                  )}
                </div>
              )}

            {event.entity_list.topics && event.entity_list.topics.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-xs text-gray-500 mr-1">Topics:</span>
                {event.entity_list.topics.slice(0, 5).map((topic, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-green-50 text-green-700 rounded"
                  >
                    {topic}
                  </span>
                ))}
                {event.entity_list.topics.length > 5 && (
                  <span className="text-xs text-gray-400">
                    +{event.entity_list.topics.length - 5} more
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Expand/Collapse button */}
        {event.full_text && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}

        {/* Expanded content */}
        {isExpanded && event.full_text && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {event.full_text}
            </p>

            {/* Sources */}
            {event.source_list && event.source_list.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 mb-1">Sources:</p>
                <ul className="space-y-1">
                  {event.source_list.map((source, idx) => (
                    <li key={idx} className="text-xs">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 hover:underline"
                      >
                        {source.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cluster indicator */}
        {event.cluster_id && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              <span className="font-medium">Multi-source event</span> - Multiple
              reports about this incident
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

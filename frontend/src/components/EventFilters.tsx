/**
 * Event filters component.
 */
import { EventCategory, Sentiment, EventFilters as EventFiltersType } from '../types';
import { getCategoryLabel } from '../utils/formatting';

interface EventFiltersProps {
  filters: EventFiltersType;
  onChange: (filters: EventFiltersType) => void;
}

const categories: EventCategory[] = [
  'protest',
  'crime',
  'religious_freedom',
  'cultural_tension',
  'political',
  'infrastructure',
  'health',
  'migration',
  'economic',
  'weather',
  'community_event',
  'other',
];

const sentiments: Sentiment[] = ['positive', 'neutral', 'negative'];

export default function EventFilters({ filters, onChange }: EventFiltersProps) {
  const handleCategoryChange = (category: EventCategory | '') => {
    onChange({
      ...filters,
      category: category || undefined,
      page: 1,
    });
  };

  const handleSentimentChange = (sentiment: Sentiment | '') => {
    onChange({
      ...filters,
      sentiment: sentiment || undefined,
      page: 1,
    });
  };

  const handleLocationChange = (location: string) => {
    onChange({
      ...filters,
      location_name: location || undefined,
      page: 1,
    });
  };

  const handleRelevanceChange = (relevance: string) => {
    onChange({
      ...filters,
      min_relevance: relevance ? parseFloat(relevance) : undefined,
      page: 1,
    });
  };

  const handleClearFilters = () => {
    onChange({
      page: 1,
      page_size: filters.page_size,
    });
  };

  const hasActiveFilters =
    filters.category ||
    filters.sentiment ||
    filters.location_name ||
    filters.min_relevance !== undefined;

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Category filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            value={filters.category || ''}
            onChange={(e) => handleCategoryChange(e.target.value as EventCategory | '')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {getCategoryLabel(cat)}
              </option>
            ))}
          </select>
        </div>

        {/* Sentiment filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sentiment
          </label>
          <select
            value={filters.sentiment || ''}
            onChange={(e) => handleSentimentChange(e.target.value as Sentiment | '')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All sentiments</option>
            {sentiments.map((sent) => (
              <option key={sent} value={sent}>
                {sent.charAt(0).toUpperCase() + sent.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Location filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <input
            type="text"
            value={filters.location_name || ''}
            onChange={(e) => handleLocationChange(e.target.value)}
            placeholder="Search location..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
        </div>

        {/* Relevance filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min. Relevance
          </label>
          <select
            value={filters.min_relevance !== undefined ? filters.min_relevance : ''}
            onChange={(e) => handleRelevanceChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All events</option>
            <option value="0.8">High (0.8+)</option>
            <option value="0.5">Medium (0.5+)</option>
            <option value="0.3">Low (0.3+)</option>
          </select>
        </div>
      </div>
    </div>
  );
}

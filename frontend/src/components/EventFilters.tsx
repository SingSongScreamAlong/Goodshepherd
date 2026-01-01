/**
 * Event filters component.
 * Dark theme with glass-morphism styling.
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
    <div className="glass-card p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filters
        </h3>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-primary-400 hover:text-primary-300 font-medium transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Category filter */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Category
          </label>
          <select
            value={filters.category || ''}
            onChange={(e) => handleCategoryChange(e.target.value as EventCategory | '')}
            className="input-dark w-full text-sm"
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
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Sentiment
          </label>
          <select
            value={filters.sentiment || ''}
            onChange={(e) => handleSentimentChange(e.target.value as Sentiment | '')}
            className="input-dark w-full text-sm"
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
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Location
          </label>
          <input
            type="text"
            value={filters.location_name || ''}
            onChange={(e) => handleLocationChange(e.target.value)}
            placeholder="Search location..."
            className="input-dark w-full text-sm"
          />
        </div>

        {/* Relevance filter */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Min. Relevance
          </label>
          <select
            value={filters.min_relevance !== undefined ? filters.min_relevance : ''}
            onChange={(e) => handleRelevanceChange(e.target.value)}
            className="input-dark w-full text-sm"
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

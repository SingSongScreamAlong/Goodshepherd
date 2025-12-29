/**
 * Indicator Trends Widget - Shows concerning and trending indicators.
 */
import { useConcerningIndicators, useTrendingIndicators } from '../hooks/useWorldAwareness';
import { useState } from 'react';

type TabType = 'concerning' | 'trending';

export default function IndicatorTrendsWidget() {
    const [activeTab, setActiveTab] = useState<TabType>('concerning');
    const { indicators: concerningIndicators, isLoading: loadingConcerning } = useConcerningIndicators();
    const { indicators: trendingIndicators, isLoading: loadingTrending } = useTrendingIndicators('increasing');

    const isLoading = loadingConcerning || loadingTrending;
    const indicators = activeTab === 'concerning' ? concerningIndicators : trendingIndicators;

    const getTrendIcon = (trend: string, delta?: number) => {
        if (delta === undefined || delta === null) return null;
        if (trend === 'increasing' || delta > 0) return <span className="text-red-500">↑</span>;
        if (trend === 'decreasing' || delta < 0) return <span className="text-green-500">↓</span>;
        return <span className="text-gray-400">→</span>;
    };

    const getDomainEmoji = (domain: string) => {
        const emojis: Record<string, string> = {
            security: '🛡️',
            migration: '🚶',
            geopolitical: '🌐',
            economic: '💰',
            infrastructure: '🏗️',
            health: '🏥',
            environmental: '🌿',
        };
        return emojis[domain] || '📊';
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="space-y-3">
                        <div className="h-12 bg-gray-200 rounded"></div>
                        <div className="h-12 bg-gray-200 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Indicators</h2>
                <div className="flex rounded-lg overflow-hidden border">
                    <button
                        onClick={() => setActiveTab('concerning')}
                        className={`px-3 py-1 text-xs font-medium transition-colors ${activeTab === 'concerning'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-white text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        Concerning ({concerningIndicators.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('trending')}
                        className={`px-3 py-1 text-xs font-medium transition-colors ${activeTab === 'trending'
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-white text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        Trending ↑
                    </button>
                </div>
            </div>

            {indicators.length === 0 ? (
                <div className="text-center py-6">
                    <span className="text-4xl mb-2 block">📊</span>
                    <p className="text-sm text-gray-600">
                        {activeTab === 'concerning' ? 'No concerning indicators' : 'No significant trends'}
                    </p>
                </div>
            ) : (
                <div className="space-y-2">
                    {indicators.slice(0, 6).map((indicator) => (
                        <div
                            key={indicator.id}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                            <div className="flex items-center space-x-3">
                                <span className="text-lg">{getDomainEmoji(indicator.domain)}</span>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{indicator.name}</p>
                                    <p className="text-xs text-gray-500 capitalize">{indicator.domain}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="flex items-center space-x-1">
                                    <span className={`text-lg font-bold ${indicator.value > 70 ? 'text-red-600' : 'text-gray-900'}`}>
                                        {indicator.value.toFixed(0)}
                                    </span>
                                    {getTrendIcon(indicator.trend, indicator.delta_7d)}
                                </div>
                                {indicator.delta_7d !== null && indicator.delta_7d !== undefined && (
                                    <span className={`text-xs ${indicator.delta_7d > 0 ? 'text-red-500' : 'text-green-500'}`}>
                                        {indicator.delta_7d > 0 ? '+' : ''}{indicator.delta_7d.toFixed(1)} (7d)
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}

                    {indicators.length > 6 && (
                        <p className="text-xs text-gray-500 text-center pt-2">
                            +{indicators.length - 6} more indicators
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}

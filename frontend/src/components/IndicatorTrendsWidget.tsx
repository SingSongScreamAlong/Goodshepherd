/**
 * Indicator Trends Widget - Shows concerning and trending indicators.
 * Dark theme with glass-morphism cards.
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
        if (trend === 'increasing' || delta > 0) {
            return (
                <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
            );
        }
        if (trend === 'decreasing' || delta < 0) {
            return (
                <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
            );
        }
        return <span className="text-gray-500">→</span>;
    };

    const getDomainIcon = (domain: string) => {
        const icons: Record<string, string> = {
            security: '🛡️',
            migration: '🚶',
            geopolitical: '🌐',
            economic: '💰',
            infrastructure: '🏗️',
            health: '🏥',
            environmental: '🌿',
        };
        return icons[domain] || '📊';
    };

    if (isLoading) {
        return (
            <div className="glass-card p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-slate-700 rounded w-1/3 mb-4"></div>
                    <div className="space-y-3">
                        <div className="h-12 bg-slate-700 rounded"></div>
                        <div className="h-12 bg-slate-700 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center">
                    <svg className="w-5 h-5 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Indicators
                </h2>
                <div className="flex rounded-lg overflow-hidden border border-white/10">
                    <button
                        onClick={() => setActiveTab('concerning')}
                        className={`px-3 py-1.5 text-xs font-medium transition-all ${activeTab === 'concerning'
                                ? 'bg-red-500/20 text-red-400 border-red-500/30'
                                : 'bg-slate-800 text-gray-400 hover:bg-slate-700 hover:text-gray-300'
                            }`}
                    >
                        Concerning ({concerningIndicators.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('trending')}
                        className={`px-3 py-1.5 text-xs font-medium transition-all ${activeTab === 'trending'
                                ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                                : 'bg-slate-800 text-gray-400 hover:bg-slate-700 hover:text-gray-300'
                            }`}
                    >
                        Trending ↑
                    </button>
                </div>
            </div>

            {indicators.length === 0 ? (
                <div className="text-center py-8 bg-slate-800/50 border border-white/5 rounded-lg">
                    <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                    </div>
                    <p className="text-sm text-gray-400">
                        {activeTab === 'concerning' ? 'No concerning indicators' : 'No significant trends'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {indicators.slice(0, 6).map((indicator) => (
                        <div
                            key={indicator.id}
                            className="flex items-center justify-between p-3 bg-slate-800/50 border border-white/5 rounded-lg hover:border-white/10 transition-all"
                        >
                            <div className="flex items-center space-x-3">
                                <span className="text-lg">{getDomainIcon(indicator.domain)}</span>
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-white truncate">{indicator.name}</p>
                                    <p className="text-xs text-gray-500 capitalize">{indicator.domain}</p>
                                </div>
                            </div>
                            <div className="text-right flex-shrink-0 ml-3">
                                <div className="flex items-center space-x-1">
                                    <span className={`text-lg font-bold ${indicator.value > 70 ? 'text-red-400' : 'text-white'}`}>
                                        {indicator.value.toFixed(0)}
                                    </span>
                                    {getTrendIcon(indicator.trend, indicator.delta_7d)}
                                </div>
                                {indicator.delta_7d !== null && indicator.delta_7d !== undefined && (
                                    <span className={`text-xs ${indicator.delta_7d > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                        {indicator.delta_7d > 0 ? '+' : ''}{indicator.delta_7d.toFixed(1)} (7d)
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {indicators.length > 6 && (
                <p className="text-xs text-gray-500 text-center pt-4">
                    +{indicators.length - 6} more indicators
                </p>
            )}
        </div>
    );
}

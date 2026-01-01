/**
 * Region Status Widget - Shows critical and elevated regions.
 * Dark theme with glass-morphism cards and status glow effects.
 */
import { useCriticalRegions, useElevatedRegions } from '../hooks/useWorldAwareness';

export default function RegionStatusWidget() {
    const { regions: criticalRegions, isLoading: loadingCritical } = useCriticalRegions();
    const { regions: elevatedRegions, isLoading: loadingElevated } = useElevatedRegions();

    const isLoading = loadingCritical || loadingElevated;

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

    const hasRegions = criticalRegions.length > 0 || elevatedRegions.length > 0;

    return (
        <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center">
                    <svg className="w-5 h-5 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Region Status
                </h2>
                <div className="flex items-center space-x-3 text-sm">
                    <span className="flex items-center px-2 py-1 bg-red-500/10 border border-red-500/20 rounded-full">
                        <span className="w-2 h-2 rounded-full bg-red-500 mr-1.5 shadow-sm shadow-red-500/50" />
                        <span className="text-red-400">{criticalRegions.length}</span>
                    </span>
                    <span className="flex items-center px-2 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full">
                        <span className="w-2 h-2 rounded-full bg-amber-500 mr-1.5 shadow-sm shadow-amber-500/50" />
                        <span className="text-amber-400">{elevatedRegions.length}</span>
                    </span>
                </div>
            </div>

            {!hasRegions ? (
                <div className="text-center py-8 bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <p className="text-sm text-emerald-400 font-medium">All regions stable</p>
                    <p className="text-xs text-gray-500 mt-1">No active concerns</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {/* Critical Regions */}
                    {criticalRegions.map((region) => (
                        <div
                            key={region.id}
                            className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20 hover:border-red-500/40 transition-all duration-200 pulse-critical"
                        >
                            <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
                                    <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                </div>
                                <div>
                                    <p className="font-medium text-white">{region.name}</p>
                                    <p className="text-xs text-gray-400">Risk: {region.composite_risk.toFixed(0)}%</p>
                                </div>
                            </div>
                            <span className="status-badge status-critical text-[10px]">
                                CRITICAL
                            </span>
                        </div>
                    ))}

                    {/* Elevated Regions */}
                    {elevatedRegions.slice(0, 5).map((region) => (
                        <div
                            key={region.id}
                            className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 hover:border-amber-500/40 transition-all duration-200"
                        >
                            <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center">
                                    <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div>
                                    <p className="font-medium text-white">{region.name}</p>
                                    <p className="text-xs text-gray-400">Risk: {region.composite_risk.toFixed(0)}%</p>
                                </div>
                            </div>
                            <span className="status-badge status-warning text-[10px]">
                                ELEVATED
                            </span>
                        </div>
                    ))}

                    {elevatedRegions.length > 5 && (
                        <p className="text-xs text-gray-500 text-center pt-2">
                            +{elevatedRegions.length - 5} more elevated regions
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}

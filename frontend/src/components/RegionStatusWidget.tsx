/**
 * Region Status Widget - Shows critical and elevated regions.
 */
import { useCriticalRegions, useElevatedRegions } from '../hooks/useWorldAwareness';
import { getStatusColor } from '../types/worldAwareness';

export default function RegionStatusWidget() {
    const { regions: criticalRegions, isLoading: loadingCritical } = useCriticalRegions();
    const { regions: elevatedRegions, isLoading: loadingElevated } = useElevatedRegions();

    const isLoading = loadingCritical || loadingElevated;

    if (isLoading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="space-y-3">
                        <div className="h-10 bg-gray-200 rounded"></div>
                        <div className="h-10 bg-gray-200 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    const hasRegions = criticalRegions.length > 0 || elevatedRegions.length > 0;

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Region Status</h2>
                <div className="flex items-center space-x-2 text-sm">
                    <span className="flex items-center">
                        <span className="w-3 h-3 rounded-full bg-red-500 mr-1"></span>
                        {criticalRegions.length}
                    </span>
                    <span className="flex items-center">
                        <span className="w-3 h-3 rounded-full bg-yellow-500 mr-1"></span>
                        {elevatedRegions.length}
                    </span>
                </div>
            </div>

            {!hasRegions ? (
                <div className="text-center py-6">
                    <span className="text-4xl mb-2 block">✅</span>
                    <p className="text-sm text-gray-600">All regions stable</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {/* Critical Regions */}
                    {criticalRegions.map((region) => (
                        <div
                            key={region.id}
                            className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor('red')}`}
                        >
                            <div className="flex items-center space-x-2">
                                <span className="text-lg">🔴</span>
                                <div>
                                    <p className="font-medium text-gray-900">{region.name}</p>
                                    <p className="text-xs text-gray-600">Risk: {region.composite_risk.toFixed(0)}%</p>
                                </div>
                            </div>
                            <span className="text-xs font-semibold uppercase bg-red-600 text-white px-2 py-1 rounded">
                                CRITICAL
                            </span>
                        </div>
                    ))}

                    {/* Elevated Regions */}
                    {elevatedRegions.slice(0, 5).map((region) => (
                        <div
                            key={region.id}
                            className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor('yellow')}`}
                        >
                            <div className="flex items-center space-x-2">
                                <span className="text-lg">🟡</span>
                                <div>
                                    <p className="font-medium text-gray-900">{region.name}</p>
                                    <p className="text-xs text-gray-600">Risk: {region.composite_risk.toFixed(0)}%</p>
                                </div>
                            </div>
                            <span className="text-xs font-semibold uppercase bg-yellow-600 text-white px-2 py-1 rounded">
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

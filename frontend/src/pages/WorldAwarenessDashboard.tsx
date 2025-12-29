/**
 * World Awareness Dashboard - Live Operational Picture.
 */
import { useRegions } from '../hooks/useWorldAwareness';
import RegionStatusWidget from '../components/RegionStatusWidget';
import VerificationQueueWidget from '../components/VerificationQueueWidget';
import IndicatorTrendsWidget from '../components/IndicatorTrendsWidget';
import StatCard from '../components/StatCard';

export default function WorldAwarenessDashboard() {
    const { byStatus, isLoading } = useRegions();

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">World Situational Awareness</h1>
                <p className="text-gray-600">Live operational picture with region states and verification status</p>
            </div>

            {/* Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <StatCard
                    label="Stable Regions"
                    value={isLoading ? '...' : byStatus.green}
                    color="green"
                    icon={
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    }
                />
                <StatCard
                    label="Elevated Concern"
                    value={isLoading ? '...' : byStatus.yellow}
                    color="yellow"
                    icon={
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    }
                />
                <StatCard
                    label="Critical Regions"
                    value={isLoading ? '...' : byStatus.red}
                    color="red"
                    icon={
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    }
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Region Status */}
                <RegionStatusWidget />

                {/* Verification Queue */}
                <VerificationQueueWidget />
            </div>

            {/* Indicator Trends - Full Width */}
            <div className="mb-6">
                <IndicatorTrendsWidget />
            </div>

            {/* Legend */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Understanding the Dashboard</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs text-gray-600">
                    <div>
                        <span className="font-medium text-gray-900">Region Status:</span>
                        <ul className="mt-1 space-y-1">
                            <li><span className="text-green-600">●</span> Green = Stable</li>
                            <li><span className="text-yellow-600">●</span> Yellow = Elevated</li>
                            <li><span className="text-red-600">●</span> Red = Critical</li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-900">Verification Status:</span>
                        <ul className="mt-1 space-y-1">
                            <li>Unverified = &lt;40% confidence</li>
                            <li>Developing = 40-74%</li>
                            <li>Corroborated = 75%+</li>
                            <li>Confirmed = Admin verified</li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-900">Severity Levels:</span>
                        <ul className="mt-1 space-y-1">
                            <li><span className="bg-red-600 text-white px-1 rounded text-[10px]">CRITICAL</span> Immediate</li>
                            <li><span className="bg-orange-500 text-white px-1 rounded text-[10px]">HIGH</span> Urgent</li>
                            <li><span className="bg-yellow-500 text-white px-1 rounded text-[10px]">MEDIUM</span> Monitor</li>
                            <li><span className="bg-green-500 text-white px-1 rounded text-[10px]">LOW</span> Routine</li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-900">Indicators:</span>
                        <ul className="mt-1 space-y-1">
                            <li>Concerning = Value &gt;70</li>
                            <li>Trending ↑ = +5 in 7 days</li>
                            <li>Delta shows 7-day change</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}

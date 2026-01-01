/**
 * World Awareness Dashboard - Live Operational Picture.
 * Tactical dark theme with glass-morphism cards and status indicators.
 */
import { useRegions } from '../hooks/useWorldAwareness';
import RegionStatusWidget from '../components/RegionStatusWidget';
import VerificationQueueWidget from '../components/VerificationQueueWidget';
import IndicatorTrendsWidget from '../components/IndicatorTrendsWidget';
import StatCard from '../components/StatCard';

export default function WorldAwarenessDashboard() {
    const { byStatus, isLoading } = useRegions();

    return (
        <div className="max-w-7xl mx-auto animate-fade-in">
            {/* Header */}
            <div className="page-header">
                <h1 className="text-3xl font-bold text-white mb-2">
                    World Situational Awareness
                </h1>
                <p className="text-gray-400">
                    Live operational picture with region states and verification status
                </p>
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
            <div className="glass-card p-5">
                <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center">
                    <svg className="w-4 h-4 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Understanding the Dashboard
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 text-xs text-gray-400">
                    <div>
                        <span className="font-medium text-gray-200 block mb-2">Region Status</span>
                        <ul className="space-y-1.5">
                            <li className="flex items-center">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 shadow-sm shadow-emerald-500/50" />
                                Green = Stable
                            </li>
                            <li className="flex items-center">
                                <span className="w-2 h-2 rounded-full bg-amber-500 mr-2 shadow-sm shadow-amber-500/50" />
                                Yellow = Elevated
                            </li>
                            <li className="flex items-center">
                                <span className="w-2 h-2 rounded-full bg-red-500 mr-2 shadow-sm shadow-red-500/50" />
                                Red = Critical
                            </li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-200 block mb-2">Verification Status</span>
                        <ul className="space-y-1.5">
                            <li>Unverified = &lt;40% confidence</li>
                            <li>Developing = 40-74%</li>
                            <li>Corroborated = 75%+</li>
                            <li>Confirmed = Admin verified</li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-200 block mb-2">Severity Levels</span>
                        <ul className="space-y-1.5">
                            <li className="flex items-center">
                                <span className="status-badge status-critical mr-2 text-[10px] py-0">CRITICAL</span>
                                Immediate
                            </li>
                            <li className="flex items-center">
                                <span className="status-badge status-elevated mr-2 text-[10px] py-0">HIGH</span>
                                Urgent
                            </li>
                            <li className="flex items-center">
                                <span className="status-badge status-warning mr-2 text-[10px] py-0">MEDIUM</span>
                                Monitor
                            </li>
                            <li className="flex items-center">
                                <span className="status-badge status-stable mr-2 text-[10px] py-0">LOW</span>
                                Routine
                            </li>
                        </ul>
                    </div>
                    <div>
                        <span className="font-medium text-gray-200 block mb-2">Indicators</span>
                        <ul className="space-y-1.5">
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

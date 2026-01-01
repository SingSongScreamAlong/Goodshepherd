/**
 * StatCard component - displays a metric with label and optional trend.
 * Dark theme with glass-morphism and glow effects.
 */
interface StatCardProps {
  label: string | React.ReactNode;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
}

export default function StatCard({ label, value, icon, trend, color = 'blue' }: StatCardProps) {
  const iconColorClasses = {
    blue: 'bg-blue-500/20 text-blue-400 shadow-blue-500/30',
    green: 'bg-emerald-500/20 text-emerald-400 shadow-emerald-500/30',
    yellow: 'bg-amber-500/20 text-amber-400 shadow-amber-500/30',
    red: 'bg-red-500/20 text-red-400 shadow-red-500/30',
    purple: 'bg-purple-500/20 text-purple-400 shadow-purple-500/30',
    gray: 'bg-gray-500/20 text-gray-400 shadow-gray-500/30',
  };

  const trendColors = {
    up: 'text-emerald-400',
    down: 'text-red-400',
    neutral: 'text-gray-400',
  };

  const valueColors = {
    blue: 'text-white',
    green: 'text-emerald-400',
    yellow: 'text-amber-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
    gray: 'text-gray-300',
  };

  return (
    <div className="glass-card-hover p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-400">{label}</h3>
        {icon && (
          <div className={`p-2.5 rounded-lg shadow-lg ${iconColorClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
      <div className="flex items-baseline justify-between">
        <p className={`text-3xl font-bold ${valueColors[color]}`}>{value}</p>
        {trend && (
          <div className={`flex items-center text-sm font-medium ${trendColors[trend.direction]}`}>
            {trend.direction === 'up' && (
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {trend.direction === 'down' && (
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {trend.value}%
          </div>
        )}
      </div>
    </div>
  );
}

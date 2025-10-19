export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

interface SeverityConfig {
  label: string;
  icon: string;
  badgeClass: string;
  borderClass: string;
  bgClass: string;
  activeClass: string;
}

const severityConfigs: Record<SeverityLevel, SeverityConfig> = {
  low: {
    label: 'Low',
    icon: 'fas fa-info-circle',
    badgeClass: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    borderClass: 'border-blue-500',
    bgClass: 'bg-blue-500',
    activeClass: 'bg-blue-500 text-white'
  },
  medium: {
    label: 'Medium',
    icon: 'fas fa-exclamation-circle',
    badgeClass: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    borderClass: 'border-yellow-500',
    bgClass: 'bg-yellow-500',
    activeClass: 'bg-yellow-500 text-white'
  },
  high: {
    label: 'High',
    icon: 'fas fa-exclamation-triangle',
    badgeClass: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    borderClass: 'border-orange-500',
    bgClass: 'bg-orange-500',
    activeClass: 'bg-orange-500 text-white'
  },
  critical: {
    label: 'Critical',
    icon: 'fas fa-times-circle',
    badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    borderClass: 'border-red-500',
    bgClass: 'bg-red-500',
    activeClass: 'bg-red-500 text-white'
  }
};

const severityOrder: Record<SeverityLevel, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3
};

export function useSeverity() {
  const getConfig = (severity: SeverityLevel | string): SeverityConfig => {
    return severityConfigs[severity as SeverityLevel] || severityConfigs.low;
  };

  const getSeverityOrder = (severity: SeverityLevel | string): number => {
    return severityOrder[severity as SeverityLevel] ?? 3;
  };

  const getAllOptions = () => {
    return Object.entries(severityConfigs).map(([value, config]) => ({
      value: value as SeverityLevel,
      ...config
    }));
  };

  return {
    getConfig,
    getSeverityOrder,
    getAllOptions,
    severityConfigs
  };
}

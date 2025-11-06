/**
 * Formatting utilities composable
 * Provides consistent formatting functions for dates, numbers, and other data
 */

/**
 * Format a date string into relative time (e.g., "2h ago") or absolute date
 */
export function useRelativeTime(dateString: string | Date): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format a date into a readable string
 */
export function useFormattedDate(date: string | Date | null | undefined): string {
  if (!date) return 'Unknown date';

  // If already a string, try to parse it
  if (typeof date === 'string') {
    const parsed = new Date(date);
    if (isNaN(parsed.getTime())) return date; // Return as-is if invalid
    date = parsed;
  }

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format a number as a percentage
 */
export function usePercentage(value: number | undefined): string {
  if (value === undefined || value === null) return '0%';
  return (Math.round(value * 100) / 100).toFixed(2) + '%';
}

/**
 * Format a file size in bytes to human-readable format
 */
export function useFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Truncate text to a maximum length
 */
export function useTruncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * Trap focus within a modal or dialog
 * Requirement 28.2: Keyboard navigation support
 */
export function trapFocus(element: HTMLElement): () => void {
  const focusableElements = element.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );

  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable?.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable?.focus();
      }
    }
  };

  element.addEventListener('keydown', handleKeyDown);

  // Focus first element
  firstFocusable?.focus();

  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Handle keyboard navigation for interactive lists
 * Requirement 28.2: Arrow key navigation
 */
export function handleListKeyNavigation(
  event: React.KeyboardEvent,
  currentIndex: number,
  itemCount: number,
  onIndexChange: (newIndex: number) => void,
  onSelect?: () => void
): void {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault();
      onIndexChange(Math.min(currentIndex + 1, itemCount - 1));
      break;
    case 'ArrowUp':
      event.preventDefault();
      onIndexChange(Math.max(currentIndex - 1, 0));
      break;
    case 'Home':
      event.preventDefault();
      onIndexChange(0);
      break;
    case 'End':
      event.preventDefault();
      onIndexChange(itemCount - 1);
      break;
    case 'Enter':
    case ' ':
      event.preventDefault();
      onSelect?.();
      break;
  }
}

/**
 * Calculate color contrast ratio
 * Requirement 28.4: Color contrast ratios of at least 4.5:1
 */
export function getContrastRatio(color1: string, color2: string): number {
  const getLuminance = (color: string): number => {
    // Convert hex to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;

    // Calculate relative luminance
    const [rs, gs, bs] = [r, g, b].map((c) => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const l1 = getLuminance(color1);
  const l2 = getLuminance(color2);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if color contrast meets WCAG AA standards
 * Requirement 28.4: Minimum 4.5:1 for normal text
 */
export function meetsWCAGAA(
  foreground: string,
  background: string,
  isLargeText: boolean = false
): boolean {
  const ratio = getContrastRatio(foreground, background);
  return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

/**
 * Generate accessible label for data visualization
 * Requirement 28.5: Text alternatives for data visualizations
 */
export function generateChartAccessibleDescription(data: {
  title: string;
  type: 'bar' | 'line' | 'pie' | 'scatter';
  dataPoints: Array<{ label: string; value: number | string }>;
  summary?: string;
}): string {
  const { title, type, dataPoints, summary } = data;

  let description = `${title}. This is a ${type} chart. `;

  if (summary) {
    description += `${summary}. `;
  }

  description += `The chart contains ${dataPoints.length} data points: `;

  const pointDescriptions = dataPoints.map(
    (point) => `${point.label}: ${point.value}`
  );

  description += pointDescriptions.join(', ');

  return description;
}

/**
 * Create skip link for keyboard navigation
 * Requirement 28.2: Skip to main content
 */
export function createSkipLink(targetId: string, label: string = 'Skip to main content') {
  return {
    href: `#${targetId}`,
    className: "sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-primary-foreground focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
    label,
  };
}

/**
 * Manage focus restoration after modal close
 * Requirement 28.2: Focus management
 */
export class FocusManager {
  private previousFocus: HTMLElement | null = null;

  saveFocus(): void {
    this.previousFocus = document.activeElement as HTMLElement;
  }

  restoreFocus(): void {
    if (this.previousFocus && typeof this.previousFocus.focus === 'function') {
      this.previousFocus.focus();
    }
  }
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Tooltip Component
 * Reusable tooltip that shows on hover

'use client';

import { ReactNode } from 'react';

interface TooltipProps {
  children: ReactNode;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ children, content, position = 'top' }: TooltipProps) {
  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2 -mb-1 border-4 border-transparent border-b-gray-900 dark:border-b-gray-700',
    left: 'left-full top-1/2 transform -translate-y-1/2 -ml-1 border-4 border-transparent border-l-gray-900 dark:border-l-gray-700',
    right: 'right-full top-1/2 transform -translate-y-1/2 -mr-1 border-4 border-transparent border-r-gray-900 dark:border-r-gray-700',
  };

  return (
    <div className="relative group inline-block">
      {children}
      <div
        className={`absolute ${positionClasses[position]} px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 shadow-lg`}
        role="tooltip"
      >
        {content}
        <div className={`absolute ${arrowClasses[position]}`} aria-hidden="true" />
      </div>
    </div>
  );
}

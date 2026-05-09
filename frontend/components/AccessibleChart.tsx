'use client';

import { ReactNode } from 'react';

interface DataPoint {
  label: string;
  value: number | string;
}

interface AccessibleChartProps {
  children: ReactNode;
  title: string;
  description: string;
  chartType: 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap';
  data?: DataPoint[];
  summary?: string;
  className?: string;
}

export function AccessibleChart({
  children,
  title,
  description,
  chartType,
  data = [],
  summary,
  className = '',
}: AccessibleChartProps) {
  const generateAccessibleDescription = (): string => {
    let desc = `${title}. ${description}. This is a ${chartType} chart. `;

    if (summary) {
      desc += `${summary}. `;
    }

    if (data.length > 0) {
      desc += `The chart contains ${data.length} data points: `;
      const pointDescriptions = data
        .slice(0, 10)
        .map((point) => `${point.label}: ${point.value}`);
      desc += pointDescriptions.join(', ');

      if (data.length > 10) {
        desc += `, and ${data.length - 10} more data points.`;
      }
    }

    return desc;
  };

  const accessibleDescription = generateAccessibleDescription();

  return (
    <figure
      className={`relative ${className}`}
      role="img"
      aria-label={accessibleDescription}
    >
      <div aria-hidden="true">{children}</div>

      <figcaption className="sr-only">{accessibleDescription}</figcaption>

      {summary && (
        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          <p>{summary}</p>
        </div>
      )}

      {data.length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-blue-600 dark:text-blue-400 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
            View data table
          </summary>
          <div className="mt-2 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
              <caption className="sr-only">{title} data table</caption>
              <thead className="bg-gray-50 dark:bg-card">
                <tr>
                  <th
                    scope="col"
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Label
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Value
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-background divide-y divide-gray-200 dark:divide-border">
                {data.map((point, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
                      {point.label}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
                      {point.value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </figure>
  );
}

interface LegendItem {
  label: string;
  color: string;
}

interface AccessibleChartLegendProps {
  items: LegendItem[];
  title?: string;
}

export function AccessibleChartLegend({
  items,
  title = 'Chart Legend',
}: AccessibleChartLegendProps) {
  return (
    <div
      role="list"
      aria-label={title}
      className="flex flex-wrap gap-4 mt-4"
    >
      {items.map((item, index) => (
        <div
          key={index}
          role="listitem"
          className="flex items-center gap-2"
        >
          <div
            className="w-4 h-4 rounded"
            style={{ backgroundColor: item.color }}
            aria-hidden="true"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

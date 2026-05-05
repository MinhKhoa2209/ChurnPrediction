/**
 * SHAP Waterfall Chart Component
 * Requirement 12.8: Display feature contributions using SHAP values
 * 
 * Visualizes how each feature contributes to the final prediction,
 * showing the cumulative effect from base value to final prediction.
 */

'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import type { ShapValues } from '@/lib/predictions';

interface ShapWaterfallChartProps {
  shapValues: ShapValues;
}

interface WaterfallDataPoint {
  feature: string;
  contribution: number;
  cumulativeValue: number;
  isPositive: boolean;
  displayValue: string;
}

export default function ShapWaterfallChart({ shapValues }: ShapWaterfallChartProps) {
  // Combine and sort all contributions by absolute value
  const allContributions = [
    ...shapValues.top_positive,
    ...shapValues.top_negative,
  ].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  // Build waterfall data
  const waterfallData: WaterfallDataPoint[] = [];
  let cumulativeValue = shapValues.base_value;

  // Add base value
  waterfallData.push({
    feature: 'Base Value',
    contribution: shapValues.base_value,
    cumulativeValue: shapValues.base_value,
    isPositive: shapValues.base_value > 0,
    displayValue: `${(shapValues.base_value * 100).toFixed(1)}%`,
  });

  // Add each contribution
  allContributions.forEach((contrib) => {
    const newCumulative = cumulativeValue + contrib.contribution;
    waterfallData.push({
      feature: contrib.feature,
      contribution: contrib.contribution,
      cumulativeValue: newCumulative,
      isPositive: contrib.contribution > 0,
      displayValue: `${contrib.contribution > 0 ? '+' : ''}${(contrib.contribution * 100).toFixed(1)}%`,
    });
    cumulativeValue = newCumulative;
  });

  // Add final prediction value
  waterfallData.push({
    feature: 'Final Prediction',
    contribution: shapValues.prediction_value,
    cumulativeValue: shapValues.prediction_value,
    isPositive: shapValues.prediction_value > 0,
    displayValue: `${(shapValues.prediction_value * 100).toFixed(1)}%`,
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as WaterfallDataPoint;
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
            {data.feature}
          </p>
          <p className={`text-sm font-medium ${data.isPositive ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
            Contribution: {data.displayValue}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            Cumulative: {(data.cumulativeValue * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={waterfallData}
          margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey="feature"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fill: 'currentColor', fontSize: 12 }}
            className="text-gray-700 dark:text-gray-300"
          />
          <YAxis
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            tick={{ fill: 'currentColor', fontSize: 12 }}
            className="text-gray-700 dark:text-gray-300"
            label={{
              value: 'Contribution to Churn Probability',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: 'currentColor', fontSize: 12 },
              className: 'text-gray-700 dark:text-gray-300',
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
          <Bar dataKey="contribution" radius={[4, 4, 0, 0]}>
            {waterfallData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.feature === 'Base Value' || entry.feature === 'Final Prediction'
                    ? '#3b82f6' // Blue for base and final
                    : entry.isPositive
                    ? '#ef4444' // Red for positive (increases churn)
                    : '#10b981' // Green for negative (decreases churn)
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
          <span className="text-gray-700 dark:text-gray-300">Base/Final Value</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
          <span className="text-gray-700 dark:text-gray-300">Increases Churn</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
          <span className="text-gray-700 dark:text-gray-300">Decreases Churn</span>
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <p className="text-xs text-gray-600 dark:text-gray-400">
          <strong>How to read this chart:</strong> The waterfall chart shows how the prediction builds up from the base value (average prediction for all customers) 
          through each feature's contribution to reach the final prediction. Red bars push the probability higher (toward churn), 
          while green bars pull it lower (away from churn).
        </p>
      </div>
    </div>
  );
}


'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ROCCurveData } from '@/lib/models';

interface ROCCurveChartProps {
  data: ROCCurveData;
}

export default function ROCCurveChart({ data }: ROCCurveChartProps) {
  const { points, auc } = data;

  // Transform data for Recharts
  const chartData = points.map((point) => ({
    fpr: parseFloat(point.fpr.toFixed(4)),
    tpr: parseFloat(point.tpr.toFixed(4)),
    threshold: parseFloat(point.threshold.toFixed(4)),
  }));

  // Add diagonal reference line data (random classifier)
  const diagonalData = [
    { fpr: 0, tpr: 0, diagonal: 0 },
    { fpr: 1, tpr: 1, diagonal: 1 },
  ];

  // Combine data for chart
  const combinedData = chartData.map((point) => ({
    ...point,
    diagonal: point.fpr, // Diagonal line where TPR = FPR
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-card p-3 rounded-lg shadow-lg border border-gray-200 dark:border-border">
          <p className="text-sm font-semibold text-gray-900 dark:text-foreground mb-1">
            ROC Point
          </p>
          <p className="text-xs text-gray-700 dark:text-gray-300">
            <strong>FPR:</strong> {(data.fpr * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-gray-700 dark:text-gray-300">
            <strong>TPR:</strong> {(data.tpr * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-gray-700 dark:text-gray-300">
            <strong>Threshold:</strong> {data.threshold.toFixed(4)}
          </p>
        </div>
      );
    }
    return null;
  };

  // Get AUC color based on performance
  const getAUCColor = (aucValue: number): string => {
    if (aucValue >= 0.9) return 'text-green-600 dark:text-green-400';
    if (aucValue >= 0.8) return 'text-blue-600 dark:text-blue-400';
    if (aucValue >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getAUCLabel = (aucValue: number): string => {
    if (aucValue >= 0.9) return 'Excellent';
    if (aucValue >= 0.8) return 'Good';
    if (aucValue >= 0.7) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="bg-white dark:bg-card shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-foreground">
          ROC Curve
        </h2>
        <div className="text-right">
          <div className="text-sm text-gray-500 dark:text-gray-400">AUC Score</div>
          <div className={`text-2xl font-bold ${getAUCColor(auc)}`}>
            {auc.toFixed(4)}
          </div>
          <div className={`text-xs font-medium ${getAUCColor(auc)}`}>
            {getAUCLabel(auc)}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={combinedData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-700" />
            <XAxis
              dataKey="fpr"
              type="number"
              domain={[0, 1]}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              tickLine={{ stroke: 'hsl(var(--border))' }}
              label={{
                value: 'False Positive Rate (FPR)',
                position: 'insideBottom',
                offset: -5,
                fill: 'hsl(var(--muted-foreground))',
              }}
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis
              dataKey="tpr"
              type="number"
              domain={[0, 1]}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              tickLine={{ stroke: 'hsl(var(--border))' }}
              label={{
                value: 'True Positive Rate (TPR)',
                angle: -90,
                position: 'insideLeft',
                fill: 'hsl(var(--muted-foreground))',
              }}
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                color: 'hsl(var(--foreground))',
              }}
            />
            
            {/* Diagonal reference line (random classifier) */}
            <Line
              type="monotone"
              dataKey="diagonal"
              stroke="#9ca3af"
              strokeDasharray="5 5"
              dot={false}
              name="Random Classifier"
              strokeWidth={2}
            />
            
            {/* ROC Curve */}
            <Line
              type="monotone"
              dataKey="tpr"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={false}
              name="ROC Curve"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Explanation */}
      <div className="mt-4 p-4 bg-gray-50 dark:bg-background rounded-lg border border-gray-200 dark:border-border">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-foreground mb-2">
          Understanding the ROC Curve
        </h4>
        <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
          <li>
            <strong>ROC Curve:</strong> Shows the trade-off between True Positive Rate (sensitivity) and False Positive Rate
          </li>
          <li>
            <strong>AUC (Area Under Curve):</strong> Measures overall model performance (0.5 = random, 1.0 = perfect)
          </li>
          <li>
            <strong>Diagonal Line:</strong> Represents a random classifier (AUC = 0.5)
          </li>
          <li>
            <strong>Interpretation:</strong> The closer the curve is to the top-left corner, the better the model
          </li>
        </ul>
      </div>

      {/* AUC Performance Guide */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="bg-green-50 dark:bg-green-900/20 rounded p-2 border border-green-200 dark:border-green-800">
          <div className="text-xs font-medium text-green-700 dark:text-green-300">
            Excellent
          </div>
          <div className="text-xs text-green-600 dark:text-green-400">
            0.9 - 1.0
          </div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2 border border-blue-200 dark:border-blue-800">
          <div className="text-xs font-medium text-blue-700 dark:text-blue-300">
            Good
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400">
            0.8 - 0.9
          </div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded p-2 border border-yellow-200 dark:border-yellow-800">
          <div className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
            Fair
          </div>
          <div className="text-xs text-yellow-600 dark:text-yellow-400">
            0.7 - 0.8
          </div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 rounded p-2 border border-red-200 dark:border-red-800">
          <div className="text-xs font-medium text-red-700 dark:text-red-300">
            Poor
          </div>
          <div className="text-xs text-red-600 dark:text-red-400">
            &lt; 0.7
          </div>
        </div>
      </div>
    </div>
  );
}

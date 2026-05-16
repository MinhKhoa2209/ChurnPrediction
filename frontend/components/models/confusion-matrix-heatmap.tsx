
import { ConfusionMatrixData } from '@/lib/models';

interface ConfusionMatrixHeatmapProps {
  data: ConfusionMatrixData;
}

export default function ConfusionMatrixHeatmap({ data }: ConfusionMatrixHeatmapProps) {
  const { matrix, labels } = data;

  // Calculate total for percentages
  const total = matrix.flat().reduce((sum, val) => sum + val, 0);

  // Get color intensity based on value
  const getColorIntensity = (value: number, maxValue: number): string => {
    const intensity = maxValue > 0 ? value / maxValue : 0;
    
    if (intensity >= 0.75) return 'bg-blue-600 text-primary-foreground';
    if (intensity >= 0.5) return 'bg-blue-500 text-primary-foreground';
    if (intensity >= 0.25) return 'bg-blue-400 text-primary-foreground';
    return 'bg-blue-200 text-gray-900 dark:bg-blue-900 dark:text-foreground';
  };

  const maxValue = Math.max(...matrix.flat());

  // Extract confusion matrix values
  const tn = matrix[0][0]; // True Negative
  const fp = matrix[0][1]; // False Positive
  const fn = matrix[1][0]; // False Negative
  const tp = matrix[1][1]; // True Positive

  return (
    <div className="bg-white dark:bg-card shadow rounded-lg p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">
        Confusion Matrix
      </h2>

      {/* Matrix Visualization */}
      <div className="mb-6">
        <div className="inline-block">
          {/* Column Headers */}
          <div className="flex mb-2">
            <div className="w-32"></div>
            <div className="text-center font-semibold text-gray-900 dark:text-foreground" style={{ width: '280px' }}>
              Predicted Label
            </div>
          </div>
          
          <div className="flex">
            {/* Row Header */}
            <div className="flex flex-col justify-center mr-2">
              <div
                className="writing-mode-vertical text-center font-semibold text-gray-900 dark:text-foreground"
                style={{ width: '30px', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <span style={{ transform: 'rotate(-90deg)', whiteSpace: 'nowrap' }}>
                  Actual Label
                </span>
              </div>
            </div>

            {/* Matrix Grid */}
            <div>
              {/* Column Labels */}
              <div className="flex mb-1">
                <div className="w-24"></div>
                {labels.map((label) => (
                  <div
                    key={label}
                    className="w-32 text-center text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    {label}
                  </div>
                ))}
              </div>

              {/* Matrix Rows */}
              {matrix.map((row, rowIndex) => (
                <div key={rowIndex} className="flex mb-2">
                  {/* Row Label */}
                  <div className="w-24 flex items-center justify-end pr-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    {labels[rowIndex]}
                  </div>

                  {/* Matrix Cells */}
                  {row.map((value, colIndex) => (
                    <div
                      key={colIndex}
                      className={`w-32 h-32 flex flex-col items-center justify-center rounded-lg mx-1 ${getColorIntensity(
                        value,
                        maxValue
                      )}`}
                    >
                      <div className="text-3xl font-bold">{value}</div>
                      <div className="text-sm opacity-90">
                        {total > 0 ? `${((value / total) * 100).toFixed(1)}%` : '0%'}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800">
          <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">
            True Negatives (TN)
          </div>
          <div className="text-2xl font-bold text-green-900 dark:text-green-100">
            {tn}
          </div>
        </div>

        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 border border-red-200 dark:border-red-800">
          <div className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">
            False Positives (FP)
          </div>
          <div className="text-2xl font-bold text-red-900 dark:text-red-100">
            {fp}
          </div>
        </div>

        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 border border-orange-200 dark:border-orange-800">
          <div className="text-xs font-medium text-orange-700 dark:text-orange-300 mb-1">
            False Negatives (FN)
          </div>
          <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
            {fn}
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
          <div className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">
            True Positives (TP)
          </div>
          <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
            {tp}
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className="p-4 bg-gray-50 dark:bg-background rounded-lg border border-gray-200 dark:border-border">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-foreground mb-2">
          Understanding the Confusion Matrix
        </h4>
        <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
          <li>
            <strong>True Negatives (TN):</strong> Correctly predicted non-churners
          </li>
          <li>
            <strong>False Positives (FP):</strong> Incorrectly predicted as churners (Type I error)
          </li>
          <li>
            <strong>False Negatives (FN):</strong> Missed churners (Type II error - higher business cost)
          </li>
          <li>
            <strong>True Positives (TP):</strong> Correctly predicted churners
          </li>
        </ul>
      </div>
    </div>
  );
}

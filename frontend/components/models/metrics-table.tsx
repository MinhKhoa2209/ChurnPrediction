import { ModelMetrics } from '@/lib/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

interface MetricsTableProps {
  metrics: ModelMetrics;
  threshold: number;
}

const formatPercentage = (value: number) => `${(value * 100).toFixed(2)}%`;

function getScoreColor(value: number) {
  if (value >= 0.9) return 'text-emerald-600 dark:text-emerald-400';
  if (value >= 0.7) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-500 dark:text-red-400';
}

function getScoreBadge(value: number): { label: string; variant: 'secondary' | 'outline' | 'destructive' } {
  if (value >= 0.9) return { label: 'Excellent', variant: 'secondary' };
  if (value >= 0.7) return { label: 'Good', variant: 'outline' };
  return { label: 'Needs Work', variant: 'destructive' };
}

export default function MetricsTable({ metrics, threshold }: MetricsTableProps) {
  const metricsData = [
    { name: 'Accuracy', value: metrics.accuracy, description: 'Overall correctness of the model' },
    { name: 'Precision', value: metrics.precision, description: 'Proportion of positive predictions that are correct' },
    { name: 'Recall', value: metrics.recall, description: 'Proportion of actual positives correctly identified' },
    { name: 'F1-Score', value: metrics.f1_score, description: 'Harmonic mean of precision and recall' },
    { name: 'ROC-AUC', value: metrics.roc_auc, description: 'Area under the ROC curve' },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evaluation Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {metricsData.map((metric) => {
            const badge = getScoreBadge(metric.value);
            return (
              <div key={metric.name} className="rounded-lg border bg-muted/30 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">{metric.name}</span>
                  <Badge variant={badge.variant} className="text-xs">{badge.label}</Badge>
                </div>
                <p className={cn('text-2xl font-bold', getScoreColor(metric.value))}>
                  {formatPercentage(metric.value)}
                </p>
                <Progress value={metric.value * 100} className="h-1.5" />
              </div>
            );
          })}

          {/* Threshold */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Threshold</span>
              <Badge variant="outline" className="text-xs">Decision</Badge>
            </div>
            <p className="text-2xl font-bold text-primary">{threshold.toFixed(2)}</p>
            <p className="text-xs text-muted-foreground">Classification boundary</p>
          </div>
        </div>

        {/* Detailed Table */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Metric</TableHead>
              <TableHead className="text-right">Value</TableHead>
              <TableHead className="hidden md:table-cell">Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {metricsData.map((metric) => (
              <TableRow key={metric.name}>
                <TableCell className="font-medium">{metric.name}</TableCell>
                <TableCell className="text-right">
                  <span className={cn('font-semibold', getScoreColor(metric.value))}>
                    {formatPercentage(metric.value)}
                  </span>
                </TableCell>
                <TableCell className="hidden md:table-cell text-muted-foreground text-sm">
                  {metric.description}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" />≥ 90% Excellent</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-500" />70–89% Good</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500" />&lt; 70% Needs Work</span>
        </div>
      </CardContent>
    </Card>
  );
}

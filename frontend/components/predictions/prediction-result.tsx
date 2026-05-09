'use client';

import { getProbabilityColor, type PredictionResponse } from '@/lib/predictions';
import ShapWaterfallChart from './shap-waterfall-chart';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { RefreshCw, Info, TrendingDown, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PredictionResultProps {
  prediction: PredictionResponse;
  onReset: () => void;
  userRole: string;
}

export default function PredictionResult({ prediction, onReset, userRole }: PredictionResultProps) {
  const probabilityPercent = (prediction.probability * 100).toFixed(1);
  const probabilityNum = prediction.probability * 100;
  const thresholdPercent = (prediction.threshold * 100).toFixed(0);
  const colors = getProbabilityColor(prediction.probability);
  const isChurn = prediction.prediction === 'Churn';

  const riskVariant = prediction.probability < 0.3 ? 'secondary'
    : prediction.probability < 0.7 ? 'outline'
    : 'destructive';

  const recommendation = prediction.probability < 0.3
    ? 'Low churn risk. Continue standard engagement and monitor for changes.'
    : prediction.probability < 0.7
    ? 'Medium churn risk. Consider proactive engagement — personalized offers or check-in calls.'
    : 'High churn risk. Immediate retention action recommended — dedicated account management or special offers.';

  return (
    <div className="space-y-6">
      {/* Main Result Card */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <CardTitle>Prediction Result</CardTitle>
          <Button variant="outline" size="sm" onClick={onReset}>
            <RefreshCw className="h-4 w-4 mr-2" />
            New Prediction
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Probability Display */}
          <div className={cn(
            'rounded-xl p-6 text-center border',
            isChurn
              ? 'bg-red-50 dark:bg-red-900/15 border-red-200 dark:border-red-800'
              : 'bg-emerald-50 dark:bg-emerald-900/15 border-emerald-200 dark:border-emerald-800'
          )}>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Churn Probability</p>
            <p className={cn(
              'text-7xl font-bold tracking-tight mb-3',
              isChurn ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'
            )}>
              {probabilityPercent}%
            </p>
            <Badge variant={riskVariant} className="text-sm px-3 py-1">
              {colors.label}
            </Badge>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Risk Level</span>
              <span className="font-medium">{probabilityPercent}%</span>
            </div>
            <Progress
              value={probabilityNum}
              className={cn('h-2', isChurn ? '[&>div]:bg-red-500' : '[&>div]:bg-emerald-500')}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0% Low</span>
              <span className="text-amber-600">↑ {thresholdPercent}% Threshold</span>
              <span>100% High</span>
            </div>
          </div>

          <Separator />

          {/* Classification Details */}
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground font-medium">Classification</dt>
              <dd className={cn('text-base font-bold mt-1 flex items-center gap-1', isChurn ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400')}>
                {isChurn ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
                {prediction.prediction}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground font-medium">Decision Threshold</dt>
              <dd className="text-base font-semibold mt-1">{thresholdPercent}%</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Recommendation Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Recommended Action</AlertTitle>
        <AlertDescription>{recommendation}</AlertDescription>
      </Alert>

      {/* SHAP Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Feature Contributions (SHAP Values)</CardTitle>
          <p className="text-sm text-muted-foreground">
            How each customer feature contributes to the prediction.
            Red bars increase churn probability; green bars decrease it.
          </p>
        </CardHeader>
        <CardContent>
          <ShapWaterfallChart shapValues={prediction.shap_values} />
        </CardContent>
      </Card>

      {/* Key Factors */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Key Factors</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {prediction.shap_values.top_positive.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-3 flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4" />
                Factors Increasing Churn Risk
              </h4>
              <div className="space-y-2">
                {prediction.shap_values.top_positive.map((contrib, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-red-50 dark:bg-red-900/15 border border-red-200 dark:border-red-800">
                    <div className="flex-1">
                      <p className="text-sm font-medium">{contrib.feature}</p>
                      <p className="text-xs text-muted-foreground">Value: {typeof contrib.value === 'number' ? contrib.value.toFixed(2) : contrib.value}</p>
                    </div>
                    <Badge variant="destructive" className="ml-4">
                      +{(contrib.contribution * 100).toFixed(1)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {prediction.shap_values.top_negative.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 mb-3 flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4" />
                Factors Decreasing Churn Risk
              </h4>
              <div className="space-y-2">
                {prediction.shap_values.top_negative.map((contrib, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/15 border border-emerald-200 dark:border-emerald-800">
                    <div className="flex-1">
                      <p className="text-sm font-medium">{contrib.feature}</p>
                      <p className="text-xs text-muted-foreground">Value: {typeof contrib.value === 'number' ? contrib.value.toFixed(2) : contrib.value}</p>
                    </div>
                    <Badge variant="secondary" className="ml-4 text-emerald-700 dark:text-emerald-300">
                      {(contrib.contribution * 100).toFixed(1)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Prediction Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="font-medium text-muted-foreground">Prediction ID</dt>
              <dd className="font-mono text-xs mt-1 text-foreground">{prediction.id}</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Model Version ID</dt>
              <dd className="font-mono text-xs mt-1 text-foreground">{prediction.model_version_id.slice(0, 16)}...</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Created At</dt>
              <dd className="mt-1 text-foreground">{new Date(prediction.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Base Value</dt>
              <dd className="mt-1 text-foreground">{(prediction.shap_values.base_value * 100).toFixed(1)}%</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}

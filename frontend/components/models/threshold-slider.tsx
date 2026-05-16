'use client';

import { useState } from 'react';
import { Loader2, Info } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface ThresholdSliderProps {
  versionId: string;
  currentThreshold: number;
  onThresholdUpdate: (newThreshold: number) => Promise<void>;
  disabled?: boolean;
}

function getThresholdInfo(value: number): { label: string; color: string; description: string } {
  if (value < 0.4) return { label: 'Low', color: 'text-emerald-600 dark:text-emerald-400', description: 'High recall — catches more churners, more false alarms' };
  if (value < 0.6) return { label: 'Balanced', color: 'text-amber-600 dark:text-amber-400', description: 'Balanced recall and precision' };
  return { label: 'High', color: 'text-red-600 dark:text-red-400', description: 'High precision — fewer false alarms, may miss churners' };
}

export default function ThresholdSlider({ versionId, currentThreshold, onThresholdUpdate, disabled = false }: ThresholdSliderProps) {
  const [threshold, setThreshold] = useState(currentThreshold);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const handleSliderChange = (value: number[]) => {
    const newValue = value[0];
    setThreshold(newValue);
    setHasChanges(newValue !== currentThreshold);
    setError(null);
  };

  const handleUpdate = async () => {
    if (threshold === currentThreshold) return;
    try {
      setIsUpdating(true);
      setError(null);
      await onThresholdUpdate(threshold);
      setHasChanges(false);
      toast.success('Threshold updated', { description: `New threshold: ${threshold.toFixed(2)}` });
    } catch (err) {
      console.error('Error updating threshold:', err);
      const msg = err instanceof Error ? err.message : 'Failed to update threshold';
      setError(msg);
      toast.error('Update failed', { description: msg });
      setThreshold(currentThreshold);
      setHasChanges(false);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleReset = () => {
    setThreshold(currentThreshold);
    setHasChanges(false);
    setError(null);
  };

  const info = getThresholdInfo(threshold);
  const isDisabled = disabled || isUpdating;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Classification Threshold</CardTitle>
            <CardDescription className="mt-1">
              Adjust to optimize for Recall or Precision
            </CardDescription>
          </div>
          <div className="text-right">
            <p className={cn('text-4xl font-bold tabular-nums', info.color)}>
              {threshold.toFixed(2)}
            </p>
            <Badge variant="outline" className="mt-1">{info.label} Threshold</Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Slider */}
        <div className="space-y-3">
          <Slider
            min={0}
            max={1}
            step={0.01}
            value={[threshold]}
            onValueChange={handleSliderChange}
            disabled={isDisabled}
            className="w-full"
            aria-label="Classification threshold slider"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.0 — High Recall</span>
            <span>0.5 — Balanced</span>
            <span>1.0 — High Precision</span>
          </div>
        </div>

        {/* Threshold Effect Summary */}
        <div className="rounded-lg bg-muted/40 border px-4 py-3">
          <p className="text-sm text-muted-foreground">
            <span className={cn('font-semibold', info.color)}>{info.label}: </span>
            {info.description}
          </p>
        </div>

        {/* Alert */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>How threshold affects predictions</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1 text-xs mt-1">
              <li><strong>Lower (0.3–0.4):</strong> Higher Recall — catches more actual churners, but more false alarms.</li>
              <li><strong>Default (0.5):</strong> Balanced Recall and Precision.</li>
              <li><strong>Higher (0.6–0.7):</strong> Higher Precision — fewer false alarms, may miss churners.</li>
            </ul>
          </AlertDescription>
        </Alert>

        {/* Error */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>

      <CardFooter className="flex flex-col gap-4">
        <Separator />
        <div className="flex justify-between items-center w-full">
          <p className="text-xs text-muted-foreground max-w-xs">
            <strong>Tip:</strong> Missed churners often cost more than false alarms. Consider lowering the threshold to maximize retention.
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleReset} disabled={!hasChanges || isDisabled}>
              Reset
            </Button>
            <Button size="sm" onClick={handleUpdate} disabled={!hasChanges || isDisabled}>
              {isUpdating ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</> : 'Update Threshold'}
            </Button>
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}

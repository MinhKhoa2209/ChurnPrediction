import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'secondary' | 'outline';
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center text-center py-16 px-4', className)}>
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-muted mb-5">
        <div className="text-muted-foreground">{icon}</div>
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">{description}</p>
      {action && (
        <Button
          variant={action.variant ?? 'default'}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

// ── Domain-specific empty states ──────────────────────────────────────

import { FileSpreadsheet, BrainCircuit, Sparkles, Bell } from 'lucide-react';

export function NoDataEmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <EmptyState
      icon={<FileSpreadsheet className="w-8 h-8" />}
      title="No data available"
      description="Upload a dataset to get started with training models and making predictions."
      action={{ label: 'Upload Dataset', onClick: onUpload }}
    />
  );
}

export function NoModelsEmptyState({ onTrain }: { onTrain: () => void }) {
  return (
    <EmptyState
      icon={<BrainCircuit className="w-8 h-8" />}
      title="No models trained"
      description="Train machine learning models on your dataset to start making predictions."
      action={{ label: 'Train Models', onClick: onTrain }}
    />
  );
}

export function NoPredictionsEmptyState({ onPredict }: { onPredict: () => void }) {
  return (
    <EmptyState
      icon={<Sparkles className="w-8 h-8" />}
      title="No predictions yet"
      description="Use your trained models to predict customer churn for individual customers or in batches."
      action={{ label: 'Make Prediction', onClick: onPredict }}
    />
  );
}

export function NoNotificationsEmptyState() {
  return (
    <EmptyState
      icon={<Bell className="w-8 h-8" />}
      title="No notifications"
      description="You're all caught up! Notifications about training jobs and system events will appear here."
    />
  );
}

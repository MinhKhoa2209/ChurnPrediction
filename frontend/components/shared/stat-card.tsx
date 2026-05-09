import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    label?: string;
  };
  badge?: {
    label: string;
    variant?: 'default' | 'secondary' | 'destructive' | 'outline';
  };
  className?: string;
  iconClassName?: string;
}

export function StatCard({
  title,
  value,
  description,
  icon,
  trend,
  badge,
  className,
  iconClassName,
}: StatCardProps) {
  const trendPositive = trend && trend.value > 0;
  const trendNegative = trend && trend.value < 0;
  const TrendIcon = trendPositive ? TrendingUp : trendNegative ? TrendingDown : Minus;
  const trendColor = trendPositive
    ? 'text-emerald-600 dark:text-emerald-400'
    : trendNegative
    ? 'text-red-500 dark:text-red-400'
    : 'text-muted-foreground';

  return (
    <Card className={cn('hover:shadow-md transition-shadow duration-200', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div className={cn('h-9 w-9 rounded-lg flex items-center justify-center', iconClassName ?? 'bg-primary/10 text-primary')}>
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div>
            <div className="text-2xl font-bold tracking-tight text-foreground">
              {value}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            {trend && (
              <div className={cn('flex items-center gap-1 text-xs font-medium', trendColor)}>
                <TrendIcon className="h-3 w-3" />
                <span>{Math.abs(trend.value)}%{trend.label ? ` ${trend.label}` : ''}</span>
              </div>
            )}
            {badge && (
              <Badge variant={badge.variant ?? 'secondary'} className="text-xs">
                {badge.label}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

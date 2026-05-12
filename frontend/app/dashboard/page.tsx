'use client';

import { useAuthStore } from '@/lib/store/auth-store';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import {
  getDashboardMetrics,
  getChurnDistribution,
  getMonthlyChurnTrend,
  type DashboardMetrics,
  type ChurnDistribution,
  type MonthlyTrendData,
} from '@/lib/dashboard';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { announceToScreenReader } from '@/lib/accessibility';
import { StatCard } from '@/components/shared/stat-card';
import { PageHeader } from '@/components/shared/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip as ShadcnTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Users, TrendingDown, AlertTriangle, Upload, BarChart2, Sparkles, RefreshCw } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, isLoading } = useAuthStore();

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [distribution, setDistribution] = useState<ChurnDistribution | null>(null);
  const [trendData, setTrendData] = useState<MonthlyTrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const [metricsResult, distributionResult, trendResult] = await Promise.allSettled([
        getDashboardMetrics(token),
        getChurnDistribution(token),
        getMonthlyChurnTrend(token, 12),
      ]);

      // Handle each result independently — one failure doesn't block others
      if (metricsResult.status === 'fulfilled') {
        setMetrics(metricsResult.value);
      } else {
        console.warn('Dashboard metrics failed:', metricsResult.reason);
      }

      if (distributionResult.status === 'fulfilled') {
        setDistribution(distributionResult.value);
      } else {
        console.warn('Churn distribution failed:', distributionResult.reason);
      }

      if (trendResult.status === 'fulfilled') {
        setTrendData(trendResult.value);
      } else {
        console.warn('Monthly trend failed:', trendResult.reason);
      }

      // Only show error if ALL widgets failed
      const allFailed =
        metricsResult.status === 'rejected' &&
        distributionResult.status === 'rejected' &&
        trendResult.status === 'rejected';

      if (allFailed) {
        const firstError = metricsResult.reason;
        const errorMessage = firstError instanceof Error ? firstError.message : 'Failed to load dashboard data';
        setError(errorMessage);
        announceToScreenReader(`Error loading dashboard: ${errorMessage}`, 'assertive');
      } else {
        announceToScreenReader('Dashboard data loaded successfully', 'polite');
      }
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
      announceToScreenReader(`Error loading dashboard: ${errorMessage}`, 'assertive');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!isLoading && token && user) {
      queueMicrotask(() => { void loadDashboardData(); });
    }
  }, [isLoading, token, user, loadDashboardData]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-xl" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!user) return null;

  const COLORS = {
    churned: '#ef4444',
    retained: '#10b981',
    trend: 'hsl(var(--primary))',
  };

  const churnRateBadge = metrics
    ? metrics.churn_rate < 20
      ? { label: 'Low Risk', variant: 'secondary' as const }
      : metrics.churn_rate < 30
      ? { label: 'Medium Risk', variant: 'outline' as const }
      : { label: 'High Risk', variant: 'destructive' as const }
    : undefined;

  return (
    <>
      <PageHeader
        title="Dashboard Analytics"
        description="Overview of customer churn metrics and trends"
      >
        <Button
          variant="outline"
          size="sm"
          onClick={loadDashboardData}
          disabled={loading}
          aria-label="Refresh dashboard data"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </PageHeader>

      {error && (
        <Alert variant="destructive" role="alert" aria-live="assertive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button variant="link" size="sm" onClick={loadDashboardData} className="text-destructive-foreground p-0 h-auto">
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Metric Cards */}
      <section aria-labelledby="metrics-heading">
        <h2 id="metrics-heading" className="sr-only">Key Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)
          ) : metrics ? (
            <>
              <StatCard
                title="Total Customers"
                value={metrics.total_customers.toLocaleString()}
                description="Active customer base"
                icon={<Users className="h-5 w-5" />}
                iconClassName="bg-primary/10 text-primary"
              />
              <StatCard
                title="Churn Rate"
                value={`${metrics.churn_rate.toFixed(1)}%`}
                description="Current period churn rate"
                icon={<TrendingDown className="h-5 w-5" />}
                iconClassName={metrics.churn_rate < 20 ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : metrics.churn_rate < 30 ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400' : 'bg-red-100 dark:bg-red-900/30 text-red-500'}
                badge={churnRateBadge}
              />
              <StatCard
                title="At-Risk Customers"
                value={metrics.at_risk_count.toLocaleString()}
                description="Churn probability > 70%"
                icon={<AlertTriangle className="h-5 w-5" />}
                iconClassName="bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400"
              />
            </>
          ) : null}
        </div>
      </section>

      {/* Charts */}
      {!loading && (distribution || trendData.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {distribution && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Churn Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Churned', value: distribution.churned },
                        { name: 'Retained', value: distribution.retained },
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent = 0 }: { name: string; percent?: number }) =>
                        `${name}: ${(percent * 100).toFixed(1)}%`
                      }
                      outerRadius={90}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      <Cell fill={COLORS.churned} />
                      <Cell fill={COLORS.retained} />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {trendData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Monthly Churn Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis
                      dataKey="month"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => {
                        const [year, month] = value.split('-');
                        return `${month}/${year.slice(2)}`;
                      }}
                    />
                    <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--popover))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: 'var(--radius)',
                        color: 'hsl(var(--popover-foreground))',
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="churn_rate"
                      stroke={COLORS.trend}
                      strokeWidth={2}
                      name="Churn Rate (%)"
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {user.role === 'Admin' ? (
              <ShadcnTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="h-auto py-4 flex flex-col gap-2 items-center justify-center"
                    onClick={() => router.push('/data/upload')}
                  >
                    <Upload className="h-5 w-5 text-primary" />
                    <span className="text-sm font-medium">Upload Dataset</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Upload customer data in CSV format to train models</TooltipContent>
              </ShadcnTooltip>
            ) : (
              <ShadcnTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="h-auto py-4 flex flex-col gap-2 items-center justify-center"
                    onClick={() => router.push('/reports')}
                  >
                    <BarChart2 className="h-5 w-5 text-primary" />
                    <span className="text-sm font-medium">View Reports</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Review and download generated model reports</TooltipContent>
              </ShadcnTooltip>
            )}

            <ShadcnTooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  className="h-auto py-4 flex flex-col gap-2 items-center justify-center"
                  onClick={() => router.push('/models/comparison')}
                >
                  <BarChart2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-sm font-medium">Compare Models</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Compare performance metrics across different models</TooltipContent>
            </ShadcnTooltip>

            <ShadcnTooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  className="h-auto py-4 flex flex-col gap-2 items-center justify-center"
                  onClick={() => router.push('/predictions')}
                >
                  <Sparkles className="h-5 w-5 text-violet-600 dark:text-violet-400" />
                  <span className="text-sm font-medium">Make Prediction</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Predict churn probability for individual customers</TooltipContent>
            </ShadcnTooltip>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

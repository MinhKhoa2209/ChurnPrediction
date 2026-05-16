import { ModelVersionListItem } from '@/lib/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';

interface ModelVersionSelectorProps {
  versions: ModelVersionListItem[];
  selectedVersionId: string;
  onVersionChange: (versionId: string) => void;
}

const formatDate = (dateString: string) =>
  new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });

export default function ModelVersionSelector({ versions, selectedVersionId, onVersionChange }: ModelVersionSelectorProps) {
  const selectedVersion = versions.find((v) => v.id === selectedVersionId);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-base">Model Version</CardTitle>
        {selectedVersion && (
          <Badge variant={selectedVersion.status === 'active' ? 'secondary' : 'outline'}>
            {selectedVersion.status === 'active' ? 'Active' : 'Archived'}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="version-select">Select Model Version</Label>
          <Select value={selectedVersionId} onValueChange={onVersionChange}>
            <SelectTrigger id="version-select">
              <SelectValue placeholder="Select a version" />
            </SelectTrigger>
            <SelectContent>
              {versions.map((version) => (
                <SelectItem key={version.id} value={version.id}>
                  {version.version} — {version.model_type} — F1: {(version.metrics.f1_score * 100).toFixed(1)}%
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedVersion && (
          <>
            <Separator />
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Version Details
              </h3>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">Version</dt>
                  <dd className="font-mono font-medium">{selectedVersion.version}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Model Type</dt>
                  <dd className="font-medium">{selectedVersion.model_type}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Trained At</dt>
                  <dd className="font-medium">{formatDate(selectedVersion.trained_at)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Training Time</dt>
                  <dd className="font-medium">{selectedVersion.training_time_seconds.toFixed(2)}s</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Accuracy</dt>
                  <dd className="font-medium text-emerald-600 dark:text-emerald-400">{(selectedVersion.metrics.accuracy * 100).toFixed(2)}%</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">F1-Score</dt>
                  <dd className="font-medium text-emerald-600 dark:text-emerald-400">{(selectedVersion.metrics.f1_score * 100).toFixed(2)}%</dd>
                </div>
              </dl>
            </div>
          </>
        )}

        <p className="text-xs text-muted-foreground">
          Showing 1 of {versions.length} model version{versions.length !== 1 ? 's' : ''}
        </p>
      </CardContent>
    </Card>
  );
}

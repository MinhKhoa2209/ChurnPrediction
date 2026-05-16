param(
    [switch]$Apply,
    [ValidateSet("safe", "confirmed")]
    [string]$Phase = "safe"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ChurnPrediction - Codebase Cleanup (Audit)    " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Phase : $Phase" -ForegroundColor Yellow

if ($Apply) {
    Write-Host "  Mode  : APPLY (will delete files!)" -ForegroundColor Red
} else {
    Write-Host "  Mode  : DRY RUN (preview only)" -ForegroundColor Green
}
Write-Host ""

# Phase 1: Safe to delete (zero references)
$safeTargets = @(
    "frontend\replace_dark_tokens.js",
    "frontend\replace_tokens.js",
    "frontend\public\file.svg",
    "frontend\public\globe.svg",
    "frontend\public\window.svg",
    "frontend\public\next.svg",
    "frontend\public\vercel.svg",
    "frontend\components\examples\ErrorHandlingExample.tsx",
    "backend\demo_csv_printer.py"
)

# Phase 2: Team-confirmed deletes
$confirmedTargets = @(
    "frontend\components\Skeleton.tsx",
    "frontend\components\Tooltip.tsx",
    "frontend\components\ThemeToggle.tsx",
    "frontend\components\ProgressBar.tsx",
    "frontend\components\LoadingSpinner.tsx",
    "frontend\components\EmptyState.tsx",
    "frontend\components\Navigation.tsx",
    "frontend\components\ToastProvider.tsx",
    "frontend\lib\responsive.ts",
    "frontend\lib\lazy-components.tsx"
)

# Select targets based on phase
if ($Phase -eq "safe") {
    $targets = $safeTargets
} else {
    $targets = $confirmedTargets
}

# Resolve paths and check existence
$found = @()
$notFound = @()

foreach ($target in $targets) {
    $fullPath = Join-Path $repoRoot $target
    if (Test-Path -LiteralPath $fullPath) {
        $found += @{ Relative = $target; Full = $fullPath }
    } else {
        $notFound += $target
    }
}

# Report
if ($found.Count -eq 0) {
    Write-Host "  No cleanup targets found for phase: $Phase" -ForegroundColor Green
    Write-Host "  All files already cleaned up!" -ForegroundColor Green
    exit 0
}

Write-Host "  Files found:" -ForegroundColor Yellow
Write-Host ""

foreach ($item in $found) {
    if ($Apply) {
        Write-Host "  [-] $($item.Relative)" -ForegroundColor Red
    } else {
        Write-Host "  [~] $($item.Relative)" -ForegroundColor DarkYellow
    }
}

if ($notFound.Count -gt 0) {
    Write-Host ""
    Write-Host "  Already deleted or not found:" -ForegroundColor DarkGray
    foreach ($item in $notFound) {
        Write-Host "  [ok] $item" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  Total: $($found.Count) file(s) to process" -ForegroundColor White

# Execute or preview
if (-not $Apply) {
    Write-Host ""
    Write-Host "  ----------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  DRY RUN complete. No files were modified." -ForegroundColor Green
    Write-Host "  Re-run with -Apply to actually delete files." -ForegroundColor Green
    Write-Host ""
    exit 0
}

# Safety check: ensure all paths are within repo
foreach ($item in $found) {
    $fullStr = $item.Full.ToString()
    $rootStr = $repoRoot.Path.ToString()
    if (-not $fullStr.StartsWith($rootStr, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "SAFETY: Refusing to delete outside repo: $fullStr"
    }
}

Write-Host ""
Write-Host "  Deleting files..." -ForegroundColor Red

$deleted = 0
foreach ($item in $found) {
    try {
        Remove-Item -LiteralPath $item.Full -Force
        Write-Host ("  [ok] Deleted: " + $item.Relative) -ForegroundColor Green
        $deleted++
    } catch {
        Write-Host ("  [FAIL] " + $item.Relative + " - " + $_.Exception.Message) -ForegroundColor Red
    }
}

# Clean up empty directories
$emptyDirs = @(
    "frontend\components\examples"
)

foreach ($dir in $emptyDirs) {
    $dirPath = Join-Path $repoRoot $dir
    if ((Test-Path $dirPath) -and ((Get-ChildItem $dirPath -Force).Count -eq 0)) {
        Remove-Item $dirPath -Force
        Write-Host ("  [ok] Removed empty directory: " + $dir) -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "  ----------------------------------------------" -ForegroundColor DarkGray
Write-Host "  Cleanup complete! $deleted file(s) deleted." -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "    1. Run: npm run build (in frontend)" -ForegroundColor White
Write-Host "    2. Run: npm run dev (to verify dev server)" -ForegroundColor White
Write-Host "    3. Run: docker compose build (to verify Docker)" -ForegroundColor White
Write-Host ""

param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$targets = @(
    "backend.log",
    ".ruff_cache",
    "htmlcov",
    "node_modules",
    "frontend/node_modules",
    "frontend/.next",
    "frontend/.swc",
    "frontend/tsconfig.tsbuildinfo",
    "shared/dist"
)

$targets += Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -Filter "__pycache__" |
    ForEach-Object {
        $_.FullName.Substring($repoRoot.Path.Length + 1)
    }

$resolvedTargets = foreach ($target in ($targets | Sort-Object -Unique)) {
    $path = Join-Path $repoRoot $target
    if (Test-Path -LiteralPath $path) {
        Resolve-Path -LiteralPath $path
    }
}

if (-not $resolvedTargets) {
    Write-Host "No cleanup targets found."
    exit 0
}

Write-Host "Cleanup targets:"
foreach ($target in $resolvedTargets) {
    Write-Host " - $($target.Path)"
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run only. Re-run with -Apply to delete these generated local artifacts."
    exit 0
}

foreach ($target in $resolvedTargets) {
    $fullPath = $target.Path
    if (-not $fullPath.StartsWith($repoRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete outside repo: $fullPath"
    }

    Remove-Item -LiteralPath $fullPath -Recurse -Force
}

Write-Host "Cleanup complete."

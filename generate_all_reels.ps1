$ErrorActionPreference = 'Continue'

$repoRoot = $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    Write-Error "Missing virtual environment at $pythonExe. Run: python -m venv .venv"
    exit 1
}

$carouselRoot = Resolve-Path (Join-Path $repoRoot '..\output_carousel')

if (-not $carouselRoot) {
    Write-Error "Folder not found: $carouselRoot"
    exit 1
}

$jobDirs = Get-ChildItem -Path $carouselRoot -Directory | Sort-Object Name

Write-Host "Found $($jobDirs.Count) job folders under $carouselRoot"

foreach ($jobDir in $jobDirs) {
    $slideFiles = Get-ChildItem -Path $jobDir.FullName -File |
        Where-Object {
            $_.Extension.ToLower() -in @('.png', '.jpg', '.jpeg', '.webp')
        }

    if ($slideFiles.Count -lt 6) {
        Write-Host "Skipping $($jobDir.Name) - only $($slideFiles.Count) slide files found"
        continue
    }

    Write-Host ""
    Write-Host "===== Creating reel for: $($jobDir.Name) ====="

    Push-Location $repoRoot
    try {
        & $pythonExe run.py create --input-dir $jobDir.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed for $($jobDir.Name)"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Finished processing all job folders."

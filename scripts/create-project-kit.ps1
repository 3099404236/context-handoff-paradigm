param(
  [string]$OutputPath = "",
  [switch]$SkipBuild,
  [switch]$WithSlides
)

$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path (Split-Path -Parent $repoRoot) "AI-project-kit.zip"
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
if ([System.IO.Path]::GetExtension($OutputPath) -ne ".zip") {
  throw "OutputPath must end with .zip"
}

if (-not $SkipBuild) {
  $buildArgs = @{ RenderPages = @(1) }
  if ($WithSlides) { $buildArgs.WithSlides = $true }
  & (Join-Path $PSScriptRoot "build-local.ps1") @buildArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Local build failed with exit code $LASTEXITCODE"
  }
}

$workRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".workbuddy\project-kit"))
$packageRoot = [System.IO.Path]::GetFullPath((Join-Path $workRoot "AI-project-kit"))
$expectedPrefix = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".workbuddy")) + [System.IO.Path]::DirectorySeparatorChar
if (-not $packageRoot.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to clean package path outside .workbuddy: $packageRoot"
}

if (Test-Path -LiteralPath $packageRoot) {
  Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null

$rootFiles = @(
  "START_HERE.md",
  "PROJECT_REQUEST.md",
  "TEMPLATE_OPTIONS.md",
  "AGENTS.md",
  "CLAUDE.md",
  "SECRETS.md",
  "AGENT_BRIEF.md",
  "PUBLISH.md",
  "README.md",
  "publish.json",
  ".gitignore",
  ".zenodo.json",
  "CITATION.cff",
  "LICENSE"
)
foreach ($relative in $rootFiles) {
  $source = Join-Path $repoRoot $relative
  if (Test-Path -LiteralPath $source) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $packageRoot $relative) -Force
  }
}

foreach ($directory in @(".github", "code", "data", "paper", "results", "scripts")) {
  $source = Join-Path $repoRoot $directory
  if (Test-Path -LiteralPath $source) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $packageRoot $directory) -Recurse -Force
  }
}

$slidesTarget = Join-Path $packageRoot "slides"
New-Item -ItemType Directory -Force -Path $slidesTarget | Out-Null
$slideFiles = @(
  "README.md",
  "main.typ",
  "main.pdf",
  "POLISHED_STYLE.md",
  "polished-sample.pdf",
  "polished-sample.pptx",
  "polished-sample-preview.png"
)
foreach ($relative in $slideFiles) {
  $source = Join-Path $repoRoot (Join-Path "slides" $relative)
  if (Test-Path -LiteralPath $source) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $slidesTarget $relative) -Force
  }
}

$manifest = Get-ChildItem -LiteralPath $packageRoot -Recurse -File |
  ForEach-Object {
    $_.FullName.Substring($packageRoot.Length + 1).Replace(
      [System.IO.Path]::DirectorySeparatorChar,
      [char]47
    )
  } |
  Sort-Object
$manifest | Set-Content -LiteralPath (Join-Path $packageRoot "PACKAGE_MANIFEST.txt") -Encoding UTF8

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
Compress-Archive -LiteralPath $packageRoot -DestinationPath $OutputPath -CompressionLevel Optimal -Force

Write-Host "Project kit created: $OutputPath"
Write-Host "Files included: $($manifest.Count)"
if (-not $WithSlides) {
  Write-Host "Slides were packaged as optional templates but were not built. Use -WithSlides to build them."
}

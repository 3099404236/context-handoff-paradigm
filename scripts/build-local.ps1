param(
  [switch]$WithSlides,
  [int[]]$RenderPages = @(1),
  [switch]$RenderAll
)

$ErrorActionPreference = "Stop"

function Get-TypstPath {
  $cmd = Get-Command typst -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  $matches = Get-ChildItem -Path $wingetRoot -Recurse -Filter typst.exe -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
  if ($matches) { return $matches[0].FullName }

  throw "typst was not found. Install Typst or add typst.exe to PATH."
}

$publishArgs = @{
  LocalOnly = $true
}
if ($RenderAll) {
  $publishArgs.RenderAll = $true
} elseif ($RenderPages.Count -gt 0) {
  $publishArgs.RenderPages = $RenderPages
}

& (Join-Path $PSScriptRoot "publish-note.ps1") @publishArgs
if ($LASTEXITCODE -ne 0) {
  throw "Paper build failed with exit code $LASTEXITCODE"
}

if ($WithSlides) {
  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
  $typst = Get-TypstPath
  Push-Location $repoRoot
  try {
    & $typst compile slides/main.typ slides/main.pdf --root .
    if ($LASTEXITCODE -ne 0) {
      throw "Slide build failed with exit code $LASTEXITCODE"
    }
    Write-Host "Built slides/main.pdf"
  } finally {
    Pop-Location
  }
}

Write-Host "Local build completed. No GitHub or Zenodo action was performed."


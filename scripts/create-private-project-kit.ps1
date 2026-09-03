param(
  [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$secretPath = Join-Path $repoRoot ".secrets.local.json"
if (-not (Test-Path -LiteralPath $secretPath)) {
  throw "Encrypted secrets not found. Run scripts/save-secrets.ps1 first."
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path (Split-Path -Parent $repoRoot) "AI-project-kit-private.zip"
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
if ([System.IO.Path]::GetExtension($OutputPath) -ne ".zip") {
  throw "OutputPath must end with .zip"
}

$workRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".workbuddy\private-kit"))
$expectedPrefix = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".workbuddy")) + [System.IO.Path]::DirectorySeparatorChar
if (-not $workRoot.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to clean private package path outside .workbuddy: $workRoot"
}
if (Test-Path -LiteralPath $workRoot) {
  Remove-Item -LiteralPath $workRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

$baseZip = Join-Path $workRoot "base.zip"
& (Join-Path $PSScriptRoot "create-project-kit.ps1") -SkipBuild -OutputPath $baseZip

$stage = Join-Path $workRoot "stage"
Expand-Archive -LiteralPath $baseZip -DestinationPath $stage -Force
$packageRoot = Join-Path $stage "AI-project-kit"
Copy-Item -LiteralPath $secretPath -Destination (Join-Path $packageRoot ".secrets.local.json") -Force

@(
  "PRIVATE LOCAL PACKAGE",
  "This archive contains a Windows DPAPI encrypted secrets file.",
  "It only decrypts for the Windows user that created it.",
  "Do not upload this archive to GitHub or a remote chat service.",
  "This warning applies to the archive and secrets, not to a cleaned project repository.",
  "A cleaned project is public by default when the user asks to upload or publish."
) | Set-Content -LiteralPath (Join-Path $packageRoot "PRIVATE_PACKAGE_WARNING.txt") -Encoding ASCII

$manifestPath = Join-Path $packageRoot "PACKAGE_MANIFEST.txt"
$manifest = @()
if (Test-Path -LiteralPath $manifestPath) {
  $manifest += Get-Content -LiteralPath $manifestPath -Encoding UTF8
}
$manifest += ".secrets.local.json"
$manifest += "PRIVATE_PACKAGE_WARNING.txt"
$manifest | Sort-Object -Unique | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Compress-Archive -LiteralPath $packageRoot -DestinationPath $OutputPath -CompressionLevel Optimal -Force
Write-Host "Private local project kit created: $OutputPath"

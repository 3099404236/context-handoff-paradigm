param(
  [string]$OutputPath = ".secrets.local.json",
  [switch]$FromEnvironment
)

$ErrorActionPreference = "Stop"

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw "This script uses Windows DPAPI and must run on Windows."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$targetPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputPath))

function Get-EnvironmentSecret {
  param([Parameter(Mandatory = $true)][string]$Name)

  $value = [Environment]::GetEnvironmentVariable($Name, "Process")
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = [Environment]::GetEnvironmentVariable($Name, "User")
  }
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "$Name is not set in the process or user environment."
  }
  return ConvertTo-SecureString $value -AsPlainText -Force
}

function Read-SecretValue {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [switch]$UseEnvironment
  )

  if ($UseEnvironment) {
    return Get-EnvironmentSecret -Name $Name
  }
  return Read-Host "Enter $Name" -AsSecureString
}

$encrypted = [ordered]@{}
foreach ($name in @("OPENROUTER_API_KEY", "ZENODO_TOKEN")) {
  $secure = Read-SecretValue -Name $name -UseEnvironment:$FromEnvironment
  $encrypted[$name] = ConvertFrom-SecureString -SecureString $secure
}

$payload = [ordered]@{
  version = 1
  protection = "Windows DPAPI CurrentUser"
  created_at = (Get-Date).ToString("o")
  secrets = $encrypted
}

$payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $targetPath -Encoding UTF8
Write-Host "Encrypted secrets saved to $targetPath"
Write-Host "The values were not printed. This file only decrypts for the current Windows user."


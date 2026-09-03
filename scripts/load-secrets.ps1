param(
  [string]$InputPath = ".secrets.local.json",
  [string[]]$Names = @("OPENROUTER_API_KEY", "ZENODO_TOKEN")
)

$ErrorActionPreference = "Stop"

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw "This script uses Windows DPAPI and must run on Windows."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$sourcePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $InputPath))
if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw "Encrypted secrets file not found: $sourcePath"
}

$payload = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($name in $Names) {
  $encrypted = $payload.secrets.$name
  if ([string]::IsNullOrWhiteSpace($encrypted)) {
    throw "Secret not found in encrypted file: $name"
  }

  $secure = ConvertTo-SecureString $encrypted
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  $plain = $null
  try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    [Environment]::SetEnvironmentVariable($name, $plain, "Process")
  } finally {
    $plain = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
  Write-Host "$name loaded into the current process (value hidden)."
}


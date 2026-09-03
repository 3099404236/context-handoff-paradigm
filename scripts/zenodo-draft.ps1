param(
  [string]$ApiBase = "https://zenodo.org/api",
  [string]$MetadataPath = ".zenodo.json",
  [string]$PdfPath = "paper\main.pdf",
  [string]$OutputPath = "zenodo-draft.json",
  [string]$DepositionId = "",
  [string]$ArtifactBaseName = "",
  [switch]$Publish
)

$ErrorActionPreference = "Stop"

function Invoke-Zenodo {
  param(
    [Parameter(Mandatory = $true)][string]$Method,
    [Parameter(Mandatory = $true)][string]$Uri,
    [object]$Body = $null
  )

  $headers = @{ "Authorization" = "Bearer $env:ZENODO_TOKEN" }

  if ($null -eq $Body) {
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
  }

  $json = $Body | ConvertTo-Json -Depth 20
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -Body $bytes -ContentType "application/json"
}

function Upload-ZenodoFile {
  param(
    [Parameter(Mandatory = $true)][string]$BucketUrl,
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Name = $null
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "File not found: $Path"
  }

  if ([string]::IsNullOrWhiteSpace($Name)) {
    $Name = Split-Path -Leaf $Path
  }

  $escapedName = [System.Uri]::EscapeDataString($Name)
  $uri = "$BucketUrl/$escapedName"
  $headers = @{ "Authorization" = "Bearer $env:ZENODO_TOKEN" }
  return Invoke-RestMethod -Method Put -Uri $uri -Headers $headers -InFile $Path -ContentType "application/octet-stream"
}

function New-SourceArchive {
  param([string]$ArchivePath)

  $parent = Split-Path -Parent $ArchivePath
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  if (Test-Path -LiteralPath $ArchivePath) {
    Remove-Item -LiteralPath $ArchivePath -Force
  }

  & git archive --format zip --output $ArchivePath HEAD
  if ($LASTEXITCODE -ne 0) {
    throw "git archive failed with exit code $LASTEXITCODE"
  }
}

if ([string]::IsNullOrWhiteSpace($env:ZENODO_TOKEN)) {
  throw "ZENODO_TOKEN is not set in the current environment."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
  $metadataRaw = Get-Content -LiteralPath $MetadataPath -Raw -Encoding UTF8
  if ($metadataRaw -match "REPLACE_WITH") {
    throw "Zenodo metadata still contains REPLACE_WITH placeholders. Update $MetadataPath first."
  }
  $metadata = $metadataRaw | ConvertFrom-Json
  $payload = @{
    metadata = $metadata
  }
  $payload.metadata | Add-Member -NotePropertyName "prereserve_doi" -NotePropertyValue $true -Force

  if ([string]::IsNullOrWhiteSpace($DepositionId)) {
    Write-Host "Creating Zenodo draft deposition..."
    $deposition = Invoke-Zenodo -Method Post -Uri "$ApiBase/deposit/depositions" -Body $payload
  } else {
    Write-Host "Updating Zenodo draft deposition $DepositionId..."
    $deposition = Invoke-Zenodo -Method Put -Uri "$ApiBase/deposit/depositions/$DepositionId" -Body $payload
  }
  $depositionId = $deposition.id
  $bucket = $deposition.links.bucket

  if ([string]::IsNullOrWhiteSpace($ArtifactBaseName)) {
    $ArtifactBaseName = Split-Path -Leaf $repoRoot
  }
  $ArtifactBaseName = ($ArtifactBaseName -replace "[^A-Za-z0-9._-]", "-").Trim("-")
  if ([string]::IsNullOrWhiteSpace($ArtifactBaseName)) {
    $ArtifactBaseName = "project"
  }

  $archivePath = Join-Path $repoRoot ".workbuddy\zenodo\$ArtifactBaseName-source.zip"
  New-SourceArchive -ArchivePath $archivePath

  Write-Host "Uploading PDF..."
  Upload-ZenodoFile -BucketUrl $bucket -Path $PdfPath -Name "$ArtifactBaseName.pdf" | Out-Null

  Write-Host "Uploading source archive..."
  Upload-ZenodoFile -BucketUrl $bucket -Path $archivePath -Name "$ArtifactBaseName-source.zip" | Out-Null

  $deposition = Invoke-Zenodo -Method Get -Uri "$ApiBase/deposit/depositions/$depositionId"

  if ($Publish) {
    Write-Host "Publishing deposition..."
    $deposition = Invoke-Zenodo -Method Post -Uri "$ApiBase/deposit/depositions/$depositionId/actions/publish"
  }

  $result = [ordered]@{
    id = $deposition.id
    conceptrecid = $deposition.conceptrecid
    state = $deposition.state
    submitted = $deposition.submitted
    title = $deposition.title
    draft_url = $deposition.links.html
    api_url = $deposition.links.self
    reserved_doi = $deposition.metadata.prereserve_doi.doi
    record_url = $deposition.record_url
    files = @($deposition.files | ForEach-Object { $_.filename })
  }

  $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Host "Zenodo draft info saved to $OutputPath"
  Write-Host "Draft URL: $($result.draft_url)"
  Write-Host "Reserved DOI: $($result.reserved_doi)"
} finally {
  Pop-Location
}

param(
  [Parameter(Mandatory = $true)][string]$HomepageRepo,
  [Parameter(Mandatory = $true)][string]$SourcePdf,
  [Parameter(Mandatory = $true)][string]$PublishConfig,
  [string]$HomepageBaseUrl = "https://3099404236.github.io",
  [string]$Message = "Sync project to homepage",
  [switch]$SkipWait
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [string[]]$Arguments = @()
  )
  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
  }
}

function Has-GitChanges {
  $status = (& git status --porcelain)
  return -not [string]::IsNullOrWhiteSpace(($status -join "`n"))
}

function Assert-RealValue {
  param([string]$Name, [object]$Value)
  $text = [string]$Value
  if ([string]::IsNullOrWhiteSpace($text) -or $text -match '待填写|请替换|^replace-') {
    throw "publish.json field '$Name' must be filled before publishing."
  }
}

$homepageRoot = [System.IO.Path]::GetFullPath($HomepageRepo)
$sourcePdfPath = [System.IO.Path]::GetFullPath($SourcePdf)
$publishConfigPath = [System.IO.Path]::GetFullPath($PublishConfig)
if (-not (Test-Path -LiteralPath $homepageRoot)) { throw "Homepage repository not found: $homepageRoot" }
if (-not (Test-Path -LiteralPath $sourcePdfPath)) { throw "Source PDF not found: $sourcePdfPath" }
if (-not (Test-Path -LiteralPath $publishConfigPath)) { throw "Publish config not found: $publishConfigPath" }

$config = Get-Content -LiteralPath $publishConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($field in @('owner', 'repository', 'slug', 'category', 'kind', 'title', 'date', 'summary', 'abstract')) {
  Assert-RealValue $field $config.$field
}
Assert-RealValue 'version.label' $config.version.label
Assert-RealValue 'version.note' $config.version.note
if (@('research', 'tools', 'applications') -notcontains [string]$config.category) {
  throw "publish.json category must be research, tools, or applications."
}
if (@($config.authors).Count -eq 0) { throw "publish.json authors must contain at least one author." }

$slug = [string]$config.slug
$versionLabel = [string]$config.version.label
$pdfRelative = "papers/$slug-$versionLabel.pdf"
$pdfRelativeNative = $pdfRelative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
$detailRelative = "publications/$slug.html"
$githubUrl = "https://github.com/$($config.owner)/$($config.repository)"
$baseUrl = $HomepageBaseUrl.TrimEnd('/')
$publicPdfUrl = "$baseUrl/$pdfRelative"
$publicDetailUrl = "$baseUrl/$detailRelative"

Push-Location $homepageRoot
try {
  if (Has-GitChanges) { throw "Homepage repository has uncommitted changes; refusing to mix publication state." }
  Invoke-Checked "git" @("pull", "--ff-only")

  $targetPdf = Join-Path $homepageRoot $pdfRelativeNative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetPdf) | Out-Null
  Copy-Item -LiteralPath $sourcePdfPath -Destination $targetPdf -Force

  $dataPath = Join-Path $homepageRoot "data\publications.json"
  if (-not (Test-Path -LiteralPath $dataPath)) { throw "Homepage data file not found: $dataPath" }
  $items = @((Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json))
  $versionObject = [ordered]@{
    label = $versionLabel
    date = [string]$config.date
    note = [string]$config.version.note
    pdf = $pdfRelative
    slides = ""
    demo = [string]$config.version.demo
    release = ""
    doi = ""
  }
  $itemObject = [ordered]@{
    slug = $slug
    category = [string]$config.category
    kind = [string]$config.kind
    title = [string]$config.title
    authors = @($config.authors)
    date = [string]$config.date
    summary = [string]$config.summary
    abstract = [string]$config.abstract
    github = $githubUrl
    discussion = ""
    versions = @([pscustomobject]$versionObject)
  }
  $updatedItems = @($items | Where-Object { [string]$_.slug -ne $slug })
  $updatedItems += [pscustomobject]$itemObject
  $json = ConvertTo-Json -InputObject @($updatedItems) -Depth 12
  [System.IO.File]::WriteAllText($dataPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

  $builder = Join-Path $homepageRoot "scripts\build_publications.py"
  if (-not (Test-Path -LiteralPath $builder)) { throw "Homepage builder not found: $builder" }
  Invoke-Checked "python" @($builder)
  if (-not (Test-Path -LiteralPath (Join-Path $homepageRoot $detailRelative.Replace('/', '\')))) {
    throw "Homepage detail page was not generated: $detailRelative"
  }

  # The generator rewrites every detail page. The homepage repository was checked
  # clean before generation, so stage the complete generated publications folder
  # to avoid leaving line-ending-only changes behind on unrelated detail pages.
  Invoke-Checked "git" @("add", "--", $pdfRelative, "data/publications.json", "publications.html", "publications")
  & git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    Invoke-Checked "git" @("commit", "-m", $Message)
    Invoke-Checked "git" @("push")
  } else {
    Write-Host "Homepage already matches publish.json; no commit needed."
  }

  $homepageSlug = (& gh repo view --json nameWithOwner --jq ".nameWithOwner").Trim()
  if (-not $SkipWait -and -not [string]::IsNullOrWhiteSpace($homepageSlug)) {
    $headSha = (& git rev-parse HEAD).Trim()
    Start-Sleep -Seconds 4
    $runId = (& gh run list --repo $homepageSlug --commit $headSha --limit 1 --json databaseId --jq ".[0].databaseId" 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($runId)) {
      Invoke-Checked "gh" @("run", "watch", $runId.Trim(), "--repo", $homepageSlug, "--exit-status")
    }
  }

  foreach ($url in @($publicDetailUrl, $publicPdfUrl)) {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -Method Head
    if ([int]$response.StatusCode -ne 200) { throw "Public URL check failed: $url" }
    Write-Host "Public URL: $($response.StatusCode) $url"
  }
} finally {
  Pop-Location
}

param(
  [string]$Message = "Publish project update",
  [string]$HomepageRepo = "..\3099404236.github.io",
  [string]$HomepageBaseUrl = "https://3099404236.github.io",
  [string]$PublishConfig = "publish.json",
  [int[]]$RenderPages = @(),
  [switch]$RenderAll,
  [switch]$LocalOnly,
  [switch]$Private,
  [switch]$SkipHomepage,
  [switch]$SkipWait,
  [switch]$SyncHomepage
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

function Get-TypstPath {
  $cmd = Get-Command typst -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  $matches = Get-ChildItem -Path $wingetRoot -Recurse -Filter typst.exe -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
  if ($matches) { return $matches[0].FullName }
  throw "typst was not found. Install Typst or add typst.exe to PATH."
}

function Get-PdftoppmPath {
  $miktex = Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64\pdftoppm.exe"
  if (Test-Path -LiteralPath $miktex) { return $miktex }
  $cmd = Get-Command pdftoppm -ErrorAction SilentlyContinue
  if ($cmd) {
    $candidate = $cmd.Source
    if ([System.IO.Path]::GetExtension($candidate) -eq ".cmd") {
      $native = [System.IO.Path]::GetFullPath((Join-Path (Split-Path $candidate) "..\..\native\poppler\Library\bin\pdftoppm.exe"))
      if (Test-Path -LiteralPath $native) { return $native }
    }
    return $candidate
  }
  return $null
}

function Has-GitChanges {
  $status = (& git status --porcelain)
  return -not [string]::IsNullOrWhiteSpace(($status -join "`n"))
}

function Wait-LatestRun {
  param([string]$RepoSlug)
  if ($SkipWait -or [string]::IsNullOrWhiteSpace($RepoSlug)) { return }
  $headSha = (& git rev-parse HEAD).Trim()
  Start-Sleep -Seconds 4
  $runId = (& gh run list --repo $RepoSlug --commit $headSha --limit 1 --json databaseId --jq ".[0].databaseId" 2>$null)
  if (-not [string]::IsNullOrWhiteSpace($runId)) {
    Invoke-Checked "gh" @("run", "watch", $runId.Trim(), "--repo", $RepoSlug, "--exit-status")
  }
}

function Assert-NoTrackedSecrets {
  $unsafe = @(& git ls-files | Where-Object {
    $_ -match '(^|/)\.secrets\.local\.json$' -or
    $_ -match '\.(token|key)$' -or
    $_ -match '(?i)private.*\.zip$' -or
    $_ -match '本机私用.*\.zip$'
  })
  if ($unsafe.Count -gt 0) {
    throw "Refusing to publish tracked secret/private artifacts: $($unsafe -join ', ')"
  }
}

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Push-Location $repoRoot
try {
  $typst = Get-TypstPath
  Write-Host "Compiling paper/main.typ -> paper/main.pdf"
  Invoke-Checked $typst @("compile", "paper/main.typ", "paper/main.pdf")

  if ($RenderAll -or $RenderPages.Count -gt 0) {
    $pdftoppm = Get-PdftoppmPath
    if (-not $pdftoppm) {
      Write-Host "pdftoppm not found; skipping PNG render."
    } else {
      $renderDir = Join-Path $repoRoot ".workbuddy\publish-render"
      if (Test-Path -LiteralPath $renderDir) { Remove-Item -LiteralPath $renderDir -Recurse -Force }
      New-Item -ItemType Directory -Force -Path $renderDir | Out-Null
      if ($RenderAll) {
        Invoke-Checked $pdftoppm @("-png", "paper/main.pdf", (Join-Path $renderDir "page"))
      } else {
        foreach ($page in $RenderPages) {
          Invoke-Checked $pdftoppm @("-f", "$page", "-l", "$page", "-png", "paper/main.pdf", (Join-Path $renderDir "page-$page"))
        }
      }
      Write-Host "Rendered PNG pages under $renderDir"
    }
  }

  if ($LocalOnly) {
    Write-Host "LocalOnly set; stopping before every GitHub and homepage action."
    return
  }

  $publishConfigPath = Join-Path $repoRoot $PublishConfig
  if (-not (Test-Path -LiteralPath $publishConfigPath)) {
    throw "Publish config not found: $publishConfigPath"
  }
  $config = Get-Content -LiteralPath $publishConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($field in @('owner', 'repository')) {
    $value = [string]$config.$field
    if ([string]::IsNullOrWhiteSpace($value) -or $value -match '待填写|请替换|^replace-') {
      throw "publish.json field '$field' must be filled before publishing."
    }
  }

  Invoke-Checked "gh" @("auth", "status")
  if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
    Invoke-Checked "git" @("init", "-b", "main")
  }
  Assert-NoTrackedSecrets

  $repoSlug = "$($config.owner)/$($config.repository)"
  $remotes = (& git remote)
  $hasOrigin = $remotes -contains "origin"
  if (-not $hasOrigin) {
    $visibilityFlag = if ($Private) { "--private" } else { "--public" }
    Invoke-Checked "gh" @("repo", "create", $repoSlug, $visibilityFlag, "--source", ".", "--remote", "origin")
  } else {
    Invoke-Checked "git" @("pull", "--ff-only")
  }

  if (Has-GitChanges) {
    Invoke-Checked "git" @("add", "-A")
    Assert-NoTrackedSecrets
    Invoke-Checked "git" @("commit", "-m", $Message)
  } else {
    Write-Host "No project repository changes to commit."
  }

  $currentBranch = (& git branch --show-current).Trim()
  Invoke-Checked "git" @("push", "-u", "origin", $currentBranch)

  $visibility = (& gh repo view $repoSlug --json visibility --jq ".visibility").Trim().ToUpperInvariant()
  $wantedVisibility = if ($Private) { "PRIVATE" } else { "PUBLIC" }
  if ($visibility -ne $wantedVisibility) {
    $target = if ($Private) { "private" } else { "public" }
    Invoke-Checked "gh" @("repo", "edit", $repoSlug, "--visibility", $target, "--accept-visibility-change-consequences")
  }
  Write-Host "GitHub visibility: $wantedVisibility $repoSlug"
  Wait-LatestRun $repoSlug

  if (-not $SkipHomepage) {
    $homepagePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $HomepageRepo))
    & (Join-Path $PSScriptRoot "sync-homepage-project.ps1") `
      -HomepageRepo $homepagePath `
      -SourcePdf (Join-Path $repoRoot "paper\main.pdf") `
      -PublishConfig $publishConfigPath `
      -HomepageBaseUrl $HomepageBaseUrl `
      -Message "Sync $($config.repository) to homepage" `
      -SkipWait:$SkipWait
  } else {
    Write-Host "SkipHomepage set; GitHub was published without changing the personal homepage."
  }
} finally {
  Pop-Location
}

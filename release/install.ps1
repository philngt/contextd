$ErrorActionPreference = 'Stop'

if (-not $env:WIKI_RELEASE_URL) {
  Write-Error "Missing WIKI_RELEASE_URL env var.`nExample:`n`$env:WIKI_RELEASE_URL='https://.../wiki-template-latest.zip'; iwr https://.../install.ps1 -UseBasicParsing | iex"
}

$tmpDir = Join-Path $env:TEMP ("wiki-install-" + [guid]::NewGuid().ToString("N"))
$zipPath = Join-Path $tmpDir "wiki-template.zip"
$extractDir = Join-Path $tmpDir "extract"
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

try {
  Write-Host "Downloading: $($env:WIKI_RELEASE_URL)"
  Invoke-WebRequest -Uri $env:WIKI_RELEASE_URL -OutFile $zipPath

  Write-Host "Extracting package..."
  Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

  $repoRoot = Join-Path $extractDir "wiki-template"
  $installer = Join-Path $repoRoot "scripts/install-to-claude.sh"
  if (-not (Test-Path $installer)) {
    throw "Invalid artifact structure. Expected wiki-template/scripts/install-to-claude.sh"
  }

  $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
  if (-not $bashCmd) {
    throw "bash not found. Install Git Bash or WSL, then run again."
  }

  Write-Host "Running installer..."
  Push-Location $repoRoot
  try {
    & bash "scripts/install-to-claude.sh"
  }
  finally {
    Pop-Location
  }

  Write-Host "Done. Verify: type $env:USERPROFILE\.claude\wiki-global.json"
}
finally {
  if (Test-Path $tmpDir) {
    Remove-Item -Recurse -Force $tmpDir
  }
}

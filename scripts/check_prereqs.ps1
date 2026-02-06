# Checks required tools and environment variables for deployment
$errors = @()

function Test-CommandExists {
  param([string]$cmd)
  try {
    $p = Get-Command $cmd -ErrorAction Stop
    Write-Host "OK: $cmd -> $($p.Source)"
    return $true
  } catch {
    Write-Host "Missing: $cmd" -ForegroundColor Red
    return $false
  }
}

Write-Host "Checking tools..."
$errors = @()
if (-not (Test-CommandExists -cmd 'aws')) { $errors += 'aws' }
if (-not (Test-CommandExists -cmd 'pwsh')) { $errors += 'pwsh' }
if (-not (Test-CommandExists -cmd 'git')) { $errors += 'git' }
if (-not (Test-CommandExists -cmd 'python')) { $errors += 'python' }

Write-Host "Checking Python packages (virtual env recommended)..."
python -c "import boto3,botocore,passlib,flask" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "One or more Python packages missing. Run: pip install -r requirements.txt" -ForegroundColor Yellow }

Write-Host "Checking environment variables..."
$vars = @('AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','EC2_KEY_NAME','ADMIN_EMAIL','PUBLIC_SUBNET_IDS','VPC_ID','ADMIN_CIDR')
foreach ($v in $vars) {
  $val = [System.Environment]::GetEnvironmentVariable($v)
  if ([string]::IsNullOrEmpty($val)) { Write-Host "Env var not set: $v" -ForegroundColor Yellow }
  else { Write-Host "Env var set: $v -> $val" }
}

if ($errors.Count -gt 0) { Write-Host "One or more required commands are missing: $($errors -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "Prereq checks complete." -ForegroundColor Green

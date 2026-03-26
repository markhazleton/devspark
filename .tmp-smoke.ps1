$ErrorActionPreference='Continue'
$tests=@(
  @{Script='scripts/powershell/check-prerequisites.ps1';Args=@('-Help')},
  @{Script='scripts/powershell/create-new-feature.ps1';Args=@('-Help')},
  @{Script='scripts/powershell/archive-context.ps1';Args=@('-Json')},
  @{Script='scripts/powershell/evolution-context.ps1';Args=@('-Json')},
  @{Script='scripts/powershell/harvest.ps1';Args=@('-Scope','scan','-Json')},
  @{Script='scripts/powershell/migrate-to-documentation.ps1';Args=@('-DryRun')},
  @{Script='scripts/powershell/quickfix-context.ps1';Args=@('-Json')},
  @{Script='scripts/powershell/release-context.ps1';Args=@('-Json','-DryRun')},
  @{Script='scripts/powershell/setup-plan.ps1';Args=@('-Help')},
  @{Script='scripts/powershell/site-audit.ps1';Args=@('-Scope','constitution','-OutputFormat','summary')},
  @{Script='scripts/powershell/update-agent-context.ps1';Args=@()}
)
$results=foreach($t in $tests){
  $scriptPath=Join-Path (Get-Location) $t.Script
  $argList=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$scriptPath)+$t.Args
  $cmdText='pwsh '+(($argList|ForEach-Object{ if($_ -match '\s'){ '"'+$_+'"' } else { $_ } }) -join ' ')
  $outFile=[System.IO.Path]::GetTempFileName(); $errFile=[System.IO.Path]::GetTempFileName()
  $exit=1; $timedOut=$false; $startErr=$null
  try {
    $p=Start-Process -FilePath 'pwsh' -ArgumentList $argList -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile -ErrorAction Stop
    try { Wait-Process -Id $p.Id -Timeout 45 -ErrorAction Stop } catch { $timedOut=$true }
    if($timedOut -and $p -and -not $p.HasExited){ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    if($timedOut){ $exit=124 } else { $exit=$p.ExitCode }
  } catch { $startErr=$_.Exception.Message; $exit=1 }
  $stdout=@(); $stderr=@()
  if(Test-Path -LiteralPath $outFile){ $stdout=Get-Content -LiteralPath $outFile -ErrorAction SilentlyContinue }
  if(Test-Path -LiteralPath $errFile){ $stderr=Get-Content -LiteralPath $errFile -ErrorAction SilentlyContinue }
  Remove-Item -LiteralPath $outFile,$errFile -ErrorAction SilentlyContinue
  $lines=@()
  if($startErr){ $lines += $startErr }
  if($stderr){ $lines += $stderr }
  if($stdout){ $lines += $stdout }
  $lines=$lines|Where-Object{ $_ -and $_.ToString().Trim().Length -gt 0 }
  $firstErr=$lines|Where-Object{ $_ -match '(?i)(^\s*error\b|exception|failed|not recognized|cannot|invalid|parsererror|at line:)' }|Select-Object -First 1
  if(-not $firstErr -and $exit -ne 0){ $firstErr=$lines|Select-Object -First 1 }
  $status = if($exit -eq 0){'PASS'} elseif($exit -eq 124){'TIMEOUT'} else {'FAIL'}
  [pscustomobject]@{ Script=$t.Script; Command=$cmdText; ExitCode=$exit; Status=$status; KeyError=(if($firstErr){$firstErr.ToString().Trim()}else{''}) }
}
$results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath '.tmp-smoke-results.json'
$results | Format-Table -AutoSize

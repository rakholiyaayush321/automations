# ACE Before Submit Prompt Hook - Injects pattern context + logs injection for task helpfulness
# Input: prompt_text

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) { New-Item -ItemType Directory -Path $aceDir -Force | Out-Null }
$cacheFile = "$aceDir\pattern_cache.json"

if (Test-Path $cacheFile) {
    try {
        $cache = Get-Content $cacheFile | ConvertFrom-Json
        $patternCount = $cache.patternCount
        if ($patternCount -gt 0) {
            $domains = if ($cache.domains) { ($cache.domains -join ", ") } else { "" }
            $avgConf = if ($cache.avgConfidence) { $cache.avgConfidence } else { 0 }
            $domainsJson = if ($cache.domains) { ($cache.domains | ForEach-Object { "`"$_`"" }) -join ", " } else { "" }
            # Log injection event for task helpfulness tracking
            $logEntry = "{`"event`": `"search`", `"patterns_injected`": $patternCount, `"domains`": [$domainsJson], `"avg_confidence`": $avgConf, `"timestamp`": `"$(Get-Date -Format 'o')`"}"
            $logEntry | Out-File -FilePath "$aceDir\ace-relevance.jsonl" -Encoding utf8 -Append
            Write-Output '{"continue": true}'
        } else {
            Write-Output '{"continue": true}'
        }
    } catch {
        Write-Output '{"continue": true}'
    }
} else {
    Write-Output '{"continue": true}'
}

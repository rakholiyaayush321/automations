# ACE After Tab File Edit Hook - Tracks tab edits
# Input: file_path

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$filePath = if ($input.file_path) { $input.file_path } else { "" }

$entry = @{event="tab_edit"; file_path=$filePath; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\edit_trajectory.jsonl" -Encoding utf8 -Append

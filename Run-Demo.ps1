param([Parameter(ValueFromRemainingArguments = $true)][string[]]$SubtitleFiles)
$ErrorActionPreference = 'Stop'
$pythonCandidates = @('python', 'py', (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'))
$selectedPython = $null
foreach ($candidate in $pythonCandidates) {
    try {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        & $command.Source -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $selectedPython = $command.Source; break }
    } catch {
        # Windows PowerShell can turn a broken runtime's stderr into an exception.
        continue
    }
}
if (-not $selectedPython) {
    [Console]::Error.WriteLine('Python 3.10+ is required. Install Python from python.org and try again.')
    exit 2
}
if (-not $SubtitleFiles) {
    $SubtitleFiles = @((Join-Path $PSScriptRoot 'examples\clean.srt'), (Join-Path $PSScriptRoot 'examples\review-needed.srt'))
}
& $selectedPython -I (Join-Path $PSScriptRoot 'srt_check.py') @SubtitleFiles
exit $LASTEXITCODE

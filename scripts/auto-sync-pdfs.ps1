# Auto-detect new PDFs in source library
# Called by Claude Code SessionStart hook.
# Checks: is it Monday ≥ 7:00 Beijing time, and hasn't been done this ISO week?
# If yes, scans source directory, compares with pdf_sources.json, updates manifest
# with new entries, and logs the results.
#
# Stamped weekly — even if you open this project multiple times on Monday night,
# the detection only runs once per ISO week.
#
# -Force: bypass the Monday ≥ 7:00 guard and run immediately (for manual/on-demand use).

param([switch]$Force)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CacheDir = Join-Path $ProjectRoot ".cache"
$StampFile = Join-Path $CacheDir "pdf-sync-week.txt"

# Ensure cache directory exists
if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
}

# ── 1. Get current Beijing time (UTC+8) ──────────────────────────
$beijingNow = [DateTime]::UtcNow.AddHours(8)
$dayOfWeek = $beijingNow.DayOfWeek
$hour = $beijingNow.Hour

# ── 2. Get ISO week number ────────────────────────────────────────
$calendar = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$isoWeek = $calendar.GetWeekOfYear(
    $beijingNow,
    [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
    [System.DayOfWeek]::Monday
)
$isoYear = $beijingNow.Year
if ($beijingNow.Month -eq 1 -and $isoWeek -gt 50) {
    $isoYear = $isoYear - 1
}
if ($beijingNow.Month -eq 12 -and $isoWeek -eq 1) {
    $isoYear = $isoYear + 1
}

$weekKey = "$isoYear-W$($isoWeek.ToString('00'))"

# ── 3. Condition check (skippable via -Force) ─────────────────────
if (-not $Force) {
    if ($dayOfWeek -ne [System.DayOfWeek]::Monday) {
        exit 0
    }

    if ($hour -lt 7) {
        exit 0
    }
}

# ── 4. Check stamp file ───────────────────────────────────────────
if (Test-Path $StampFile) {
    $lastWeek = (Get-Content $StampFile -Raw).Trim()
    if ($lastWeek -eq $weekKey) {
        exit 0
    }
}

# ── 5. Resolve python ──────────────────────────────────────────────
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    # Fallback to miniconda python (hook env may not have conda init)
    $condaPython = "C:\Users\pc\miniconda3\python.exe"
    if (Test-Path $condaPython) {
        $pythonExe = $condaPython
    } else {
        Write-Warning "python not found — skipping PDF detection"
        exit 1
    }
}

$detectScript = Join-Path (Join-Path $ProjectRoot "scripts") "detect_new_pdfs.py"
$logFile = Join-Path $CacheDir "pdf-sync.log"
$timestamp = $beijingNow.ToString("yyyy-MM-dd HH:mm:ss")

try {
    # Run detection (--update adds new PDFs to manifest)
    $output = & $pythonExe -X utf8 $detectScript --update 2>&1 | Out-String

    # Write stamp ONLY after successful execution (prevents broken stamp on failure)
    $weekKey | Out-File -FilePath $StampFile -Encoding utf8 -NoNewline

    # Write full output to log
    "[$timestamp] PDF sync — week $weekKey" | Out-File -FilePath $logFile -Encoding utf8
    $output | Out-File -FilePath $logFile -Encoding utf8 -Append

    # Parse new count from output
    $newCount = 0
    if ($output -match "--- NEW \((\d+)\)") {
        $newCount = [int]$Matches[1]
    }

    # ── 6. Show reminders ──────────────────────────────────────────
    if ($newCount -gt 0) {
        Write-Output ""
        Write-Output "$newCount new PDF(s) detected, pdf_sources.json updated"
        Write-Output "   Week: $weekKey  |  Time: $timestamp"
        Write-Output "   Convert new papers: python scripts/link_pdfs.py <library> --convert --new-only"
        Write-Output "   Check log: cat .cache/pdf-sync.log"
        Write-Output ""
    } else {
        # Quiet — no new papers, just log it
        Write-Output ""
        Write-Output "PDF library scan complete - no new papers (week $weekKey)"
        Write-Output ""
    }
} catch {
    Remove-Item $StampFile -Force -ErrorAction SilentlyContinue
    Write-Warning "PDF detection failed: $_"
    exit 1
}

exit 0

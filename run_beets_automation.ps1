# Configuration
$IncomingDir = "C:\Users\dansh\pyProjects\AudiophileNAS\AudiophileNAS\downloads"
$LogFile = "C:\Users\dansh\pyProjects\AudiophileNAS\AudiophileNAS\beets_automation.log"
$BeetCmd = "C:\Users\dansh\pyProjects\AudiophileNAS\AudiophileNAS\venv\Scripts\beet.exe"
$ConfigFile = "C:\Users\dansh\pyProjects\AudiophileNAS\AudiophileNAS\beets_config.yaml"

# Ensure log file exists
if (-not (Test-Path $LogFile)) {
    New-Item -Path $LogFile -ItemType File | Out-Null
}

# Check if there are any files in the incoming directory
if (-not (Get-ChildItem -Path $IncomingDir -File -Recurse)) {
    # Directory is empty or has no files, exit silently
    exit 0
}

$Date = Get-Date
Add-Content -Path $LogFile -Value "----------------------------------------"
Add-Content -Path $LogFile -Value "Starting scan at $Date"

# Run Beets
# -c : Specify config file
# -q : Quiet mode
# -s : Singleton mode (treat each file individually)
# -A : Autotag (trust existing metadata, don't ask user)
try {
    & $BeetCmd -c $ConfigFile import -q -s -A $IncomingDir 2>&1 | Out-File -FilePath $LogFile -Append -Encoding utf8
}
catch {
    Add-Content -Path $LogFile -Value "Error executing beets: $_"
}

$Date = Get-Date
Add-Content -Path $LogFile -Value "Scan finished at $Date"

# setup.ps1
#
# This script programmatically creates a scheduled task on Windows to run the
# RSS feed polling script periodically. It creates a .bat file to ensure the
# Python script runs in the correct directory, then uses schtasks.exe to
# schedule the .bat file.
#
# To Run:
# 1. Open PowerShell as an Administrator.
# 2. Navigate to the project directory.
# 3. Run the command: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# 4. Run the script: .\setup.ps1

# --- Configuration ---
$TaskName = "RSS Queue Poller"
$PythonScriptName = "scraper.py"
$BatchFileName = "run_scraper.bat"

# --- Scheduling Configuration ---
# Define the schedule for the task.
$DaysOfWeek = "*" # Days to run the task. Use * for all days.
$StartTime = "08:00"                 # Time to start the task each day.
$RepetitionIntervalMinutes = 60      # How often to repeat the task, in minutes.
$RepetitionDurationHours = 14        # For how many hours to repeat the task after it starts. (e.g., 14 hours from 8am is 10pm).

# --- Script Logic ---

# Get the absolute path of the directory where this script is located.
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    # Fallback for older PowerShell versions or different execution contexts
    $ProjectRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
}

# Construct the full paths for the Python executable and the main script.
$PythonExePath = Join-Path -Path $ProjectRoot -ChildPath "venv\Scripts\python.exe"
$ScriptToRunPath = Join-Path -Path $ProjectRoot -ChildPath $PythonScriptName
$BatchFilePath = Join-Path -Path $ProjectRoot -ChildPath $BatchFileName

# Check if the venv python.exe exists. If not, exit with an error.
if (-not (Test-Path $PythonExePath)) {
    Write-Host "ERROR: Python executable not found at '$PythonExePath'."
    Write-Host "Please make sure you have created the virtual environment by running 'python -m venv venv'."
    exit 1
}

# --- Create the .bat wrapper file ---
# This batch file changes to the correct directory before running the Python script.
# This ensures that all relative file paths (like 'config/rules.json') work correctly.
$BatchFileContent = @"
@echo off
cd /d "$ProjectRoot"
"$PythonExePath" "$ScriptToRunPath"
"@

Write-Host "Creating batch file at: $BatchFilePath"
Set-Content -Path $BatchFilePath -Value $BatchFileContent

# --- Use schtasks.exe to create the scheduled task ---
# This is more reliable than the PowerShell cmdlets for complex schedules.

Write-Host "Registering scheduled task: '$TaskName'..."

# /Create: Creates a new task.
# /TN: Task Name.
# /TR: Task to Run (the full path to our .bat file).
# /SC: Schedule type (WEEKLY).
# /D: Days of the week.
# /ST: Start Time.
# /RI: Repetition Interval (in minutes).
# /DU: Repetition Duration (in HH:MM format).
# /F: Force creation and overwrite if the task already exists.
# /RL: Run Level (HIGHEST, to avoid permission issues).
# /IT: Interactive Task (runs under the logged-in user).

$RepetitionDurationFormatted = "{0:D2}:00" -f $RepetitionDurationHours
schtasks.exe /Create /TN $TaskName /TR "$BatchFilePath" /SC WEEKLY /D $DaysOfWeek /ST $StartTime /RI $RepetitionIntervalMinutes /DU $RepetitionDurationFormatted /F /RL HIGHEST /IT

# Check the exit code of the last command to see if it was successful.
if ($LASTEXITCODE -eq 0) {
    Write-Host "Task '$TaskName' has been successfully created/updated."
    Write-Host "It will run every $RepetitionIntervalMinutes minutes on all days between $StartTime for $RepetitionDurationHours hours."
    Write-Host "IMPORTANT: You should add '$BatchFileName' to your .gitignore file."
} else {
    Write-Host "ERROR: Failed to create scheduled task. schtasks.exe exited with code $LASTEXITCODE"
}

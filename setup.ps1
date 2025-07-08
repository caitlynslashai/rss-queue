# setup.ps1
#
# This script programmatically creates a scheduled task on Windows to run the
# RSS feed polling script periodically.
#
# To Run:
# 1. Open PowerShell as an Administrator.
# 2. Navigate to the project directory.
# 3. Run the command: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# 4. Run the script: .\setup.ps1

# --- Configuration ---
$TaskName = "RSS Queue Poller"
$TaskDescription = "Periodically checks RSS feeds for new articles and adds them to a priority queue."
$PythonScriptName = "scraper.py"

# --- Script Logic ---

# Get the absolute path of the directory where this script is located.
# This makes the script portable and not dependent on hardcoded paths.
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    # Fallback for older PowerShell versions or different execution contexts
    $ProjectRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
}

# Construct the full paths for the Python executable and the script to run.
$PythonExePath = Join-Path -Path $ProjectRoot -ChildPath "venv\Scripts\python.exe"
$ScriptToRunPath = Join-Path -Path $ProjectRoot -ChildPath $PythonScriptName

# Check if the venv python.exe exists. If not, exit with an error.
if (-not (Test-Path $PythonExePath)) {
    Write-Host "ERROR: Python executable not found at '$PythonExePath'."
    Write-Host "Please make sure you have created the virtual environment by running 'python -m venv venv'."
    exit 1
}

Write-Host "Project Root: $ProjectRoot"
Write-Host "Python Path: $PythonExePath"
Write-Host "Script Path: $ScriptToRunPath"

# Define the action to be performed by the task.
# It runs the python.exe from the virtual environment.
# The argument is the name of our scraper script.
# The working directory is set to the project root to ensure file paths work correctly.
$Action = New-ScheduledTaskAction -Execute $PythonExePath -Argument $ScriptToRunPath -WorkingDirectory $ProjectRoot

# Define the base trigger for the task. It starts today at 3:00 AM.
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am

# --- FIX: Set the repetition properties on the nested Repetition object ---
# It will repeat every 1 hour indefinitely.
$Trigger.Repetition.Interval = "PT1H" # Set interval to 1 hour
$Trigger.Repetition.Duration = "P0D"  # Set duration to indefinite (P0D means 0 days)


# Define the user principal under which the task will run.
# This uses the currently logged-in user's environment variable.
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Define the settings for the task.
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Check if a task with the same name already exists. If so, unregister it first.
# This allows the setup script to be run multiple times to update the task.
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "An existing task named '$TaskName' was found. It will be updated."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register the new scheduled task with the system.
Write-Host "Registering new scheduled task: '$TaskName'..."
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description $TaskDescription

Write-Host "Task '$TaskName' has been successfully created."
Write-Host "It will run every hour to check for new articles."

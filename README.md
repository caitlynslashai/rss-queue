SETUP - Windows

1. Open a PowerShell terminal **as an Administrator**.
2. Navigate to this project's root directory.
3.  Run the following command to allow the script to execute:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    ```
4. Run the setup script:
    ```powershell
    .\setup.ps1
    ```
The script will create a new task in the Windows Task Scheduler.
# Description: This script installs QView3D on Windows.
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
$programFiles = $env:Programfiles
# Change directory to the QView3D directory.
Set-Location $programFiles

# Check if the QView3D directory exists.
if (!(Test-Path "SUNY Hydra Lab"))
{
    New-Item -ItemType Directory -Name "SUNY Hydra Lab"
}
Set-Location "SUNY Hydra Lab"

if (Test-Path "QView3D")
{
    Write-Host "QView3D directory already exists. Would you like to remove it and reinstall? ([Y]es/[N]o)"
    $response = Read-Host
    if (($response -eq "y") -or ($response -eq "Y")) {
        Write-Host "Removing QView3D directory..."
        Remove-Item -Recurse -Force "QView3D"
        Write-Host "QView3D directory removed."
    }
    else {
        Write-Host "Exiting script."
        exit
    }
}
$response = "0"
while ($true)
{
    Write-Host "would you like to install the [C]lient, the [S]erver, or [B]oth?"
    $response = Read-Host
    if (($response -eq "s") -or ($response -eq "S") -or ($response -eq "c") -or ($response -eq "C") -or ($response -eq "b") -or ($response -eq "B")) {
        break
    }
    Write-Host "Invalid Input!!!"
}
$server = (($response -eq "s") -or ($response -eq "S") -or ($response -eq "b") -or ($response -eq "B"))
$client = (($response -eq "c") -or ($response -eq "C") -or ($response -eq "b") -or ($response -eq "B"))

# clone the repository
git clone https://github.com/L10nhunter/QView3D.git --branch Installer-Creation

# Change directory to the QView3D directory.
Set-Location "QView3D"

# Install Chocolatey
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
if (choco -v != $null) {
    Write-Host "Chocolatey is already installed."
}
else {
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

if ($server) {
    # install python3
    if (python -V != $null) {
        Write-Host "Python is already installed."
    }
    else {
        choco install python3 -y
        refreshenv
    }

    # install pip
    if (pip -V != $null) {
        Write-Host "pip is already installed."
    }
    else {
        choco install pip -y
        refreshenv
    }

    # install flask
    if (flask --version != $null) {
        Write-Host "Flask is already installed."
    }
    else {
        pip install flask
    }
    # Install Python dependencies. Requirements was created with pipreqs.
    pip install -r requirements.txt

    # Change directory to the server.
    Set-Location server

    # Initialize the database.
    flask db init

    # Generate a migration script.
    flask db migrate

    # Apply the migration.
    flask db upgrade

    Set-Location ..
}
if ($client) {
    # Install Node.js and npm
    if (node -v != $null) {
        Write-Host "Node.js is already installed."
    }
    else {
        choco install nodejs -y
        refreshenv
    }

    # Install nvm-windows
    if (Get-Command nvm -ErrorAction SilentlyContinue) {
        Write-Host "nvm-windows is already installed."
    }
    else {
        choco install nvm -y
        refreshenv
    }

    #check if ps2exe powershell module is installed
    if (Get-Command ps2exe -ErrorAction SilentlyContinue) {
        Write-Host "ps2exe is already installed."
    }
    else {
        Install-Module -Name ps2exe -Scope CurrentUser -Force
    }

    # Change directory to the client.
    Set-Location "client"

    # Install Node.js dependencies.
    npm install

    # Install npm-run-all as a dev dependency
    npm install --save-dev npm-run-all

    # Build the client.
    #npm run build
}
# Change directory to the root.
Set-Location ..
$command = ""
if($client -and $server){
    $command = "start"
}
elseif($client) {
    $command = "start-vue"
}
else {
    $command = "start-flask"
}
# create the QView3D.ps1 file in the program files directory and use ps2exe to create an executable
$run = @"
Set-Location '$programFiles\SUNY Hydra Lab\QView3D\client'
Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command "& { npm run $command }"' -Verb RunAs
Start-process "http://localhost:5173"
"@
$run | Out-File ".\QView3D.ps1"
Invoke-Expression "ps2exe .\QView3D.ps1 .\QView3D.exe -iconFile .\client\public\favicon2.ico -description 'QView3D Executable' -version 0.1.0 -product 'QView3D' -company 'SUNY Hydra Lab' -copyright 'MIT' -requireAdmin -noOutput"

# create shortcut to run script on the desktop
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\QView3D.lnk")
$Shortcut.TargetPath = "$programFiles\SUNY Hydra Lab\QView3D\QView3D.exe"
$Shortcut.Save()

Read-Host -Prompt 'Press Enter to exit'
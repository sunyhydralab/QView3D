# Description: This script installs QView3D on Windows.
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;

# Change directory to the QView3D directory.
Set-Location "C:\Program Files"

# Check if the QView3D directory exists.
if(!(Test-Path "SUNY Hydra Lab")) {
    New-Item -ItemType Directory -Name "SUNY Hydra Lab"
}
Set-Location "SUNY Hydra Lab"

if(Test-Path "QView3D") {
    Write-Host "QView3D directory already exists. Would you like to remove it and reinstall? (y/n)"
    $response = Read-Host
    if($response -eq "y") {
        Remove-Item -Recurse -Force "QView3D"
    } else {
        Write-Host "Exiting script."
        exit
    }
}

# clone the repository
# TODO: change this to the main branch once development is complete
git clone https://github.com/L10nhunter/QView3D.git --branch Installer-Creation

# Change directory to the QView3D directory.
Set-Location "QView3D"

# Install Chocolatey
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
if(choco -v != $null) {
    Write-Host "Chocolatey is already installed."
} else {
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Install Node.js and npm
if(node -v != $null) {
    Write-Host "Node.js is already installed."
} else {
    choco install nodejs -y
    refreshenv
}

# Install nvm-windows
if(Get-Command nvm -ErrorAction SilentlyContinue) {
    Write-Host "nvm-windows is already installed."
} else {
    choco install nvm -y --version 1.1.11
    refreshenv
}

#check if ps2exe powershell module is installed
if(Get-Command ps2exe -ErrorAction SilentlyContinue) {
    Write-Host "ps2exe is already installed."
} else {
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

# Change directory to the root.
Set-Location ..

# create the QView3D.ps1 file in the program files directory and use ps2exe to create an executable
$run = @"
Set-Location 'C:\Program Files\SUNY HydraLab\QView3D\client'
npm run dev
Start-Process "http://localhost:5173"
Read-Host -Prompt 'Press Enter to exit'
"@
$run | Out-File ".\QView3D.ps1"
Invoke-Expression "ps2exe .\QView3D.ps1 .\QView3D.exe -iconFile .\client\public\favicon2.ico -description 'QView3D Executable' -version 0.1.0 -product 'QView3D' -company 'SUNY Hydra Lab' -copyright 'MIT' -requireAdmin -noOutput"

# create shortcut to run script on the desktop
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\QView3D.lnk")
$Shortcut.TargetPath = "C:\Program Files\SUNY HydraLab\QView3D\QView3D.exe"
$Shortcut.Save()
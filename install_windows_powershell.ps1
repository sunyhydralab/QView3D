# Description: This script installs QView3D on Windows.
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;

# Change directory to the QView3D directory.
Set-Location "C:\Program Files"

# Check if the QView3D directory exists.
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
git clone https://github.com/L10nhunter/QView3D.git --branch code_cleanup

# Change directory to the QView3D directory.
Set-Location "QView3D"

# Install Chocolatey
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
if(choco -v != $null) {
    Write-Host "Chocolatey is already installed."
} else {
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Install Python and pip
if(Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Python is already installed."
} else {
    choco install python -y -ia "'/InstallDir:C:\Python'"
    # Refresh environment variables
    refreshenv
}

# Install Node.js and npm
if(node -v != $null) {
    Write-Host "Node.js is already installed."
} else {
    choco install nodejs -y -ia "'/installDirectory:C:\Program Files\nodejs'"
    # Refresh environment variables
    refreshenv
}
# create an environment variable that points to the new nodejs exe
# TODO: change folder to find the nodejs exe regardless of version
$env:node = ";C:\Program Data\nvm\22.8.0\node.exe"


# Install nvm-windows
# install nvm-windows version 1.1.11
if(Get-Command nvm -ErrorAction SilentlyContinue) {
    Write-Host "nvm-windows is already installed."
} else {
    choco install nvm -y --version 1.1.11
    # Refresh environment variables
    refreshenv
}


# Install Python dependencies. Requirements was created with pipreqs.
# check if pip is installed and install if not
if(Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Host "pip is already installed."
} else {
    choco install pip -y
    # Refresh environment variables
    refreshenv
}

pip install -r requirements.txt 

# Change directory to the server.
Set-Location server

# Initialize the database. 
flask db init 

# Generate a migration script. 
flask db migrate 

# Apply the migration. 
flask db upgrade 

# Change directory to the client.
Set-Location ../client

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
Set-Location 'C:\Program Files\QView3D\client'
npm run dev
Read-Host -Prompt 'Press Enter to exit'
"@
$run | Out-File ".\QView3D.ps1"
Invoke-Expression "ps2exe .\QView3D.ps1 .\QView3D.exe -iconFile .\client\public\favicon2.ico -description 'QView3D Executable' -version 0.1.0 -product 'QView3D' -company 'SUNY Hydra Lab' -copyright 'MIT' -requireAdmin"

# create shortcut to run script on the desktop
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\QView3D.lnk")
$Shortcut.TargetPath = "C:\Program Files\QView3D\QView3D.exe"
$Shortcut.Save()

Read-Host -Prompt "Press Enter to exit"
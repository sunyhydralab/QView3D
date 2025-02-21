# Description: This script installs winget, usbipd, and WSL2, then attaches USB devices to WSL2 and builds a Docker image.

param(
    [string]$cwd
)
# Check if running as Administrator
$adminCheck = [Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
$adminRole = [Security.Principal.WindowsBuiltInRole]::Administrator

if (-not $adminCheck.IsInRole($adminRole)) {
    # Relaunch the script as Administrator in the same PowerShell session with the same working directory
    $cwd = Get-Location
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -cwd `"$cwd`"" -Verb RunAs -Wait
    exit
}

if ($cwd) {
    Set-Location $cwd
}
# Check if winget is installed, if not, install winget
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Output "winget is not installed. Installing winget..."
    Invoke-WebRequest -Uri "https://aka.ms/getwinget" -OutFile "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    Add-AppxPackage -Path "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    winget install usbipd-win
    $cwd = Get-Location
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -cwd `"$cwd`"" -Verb RunAs -Wait
    exit
} else {
    Write-Output "winget is already installed."
}
# Check if usbipd is installed, if not, install usbipd
if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    Write-Output "usbipd is not installed. Installing usbipd..."
    winget install usbipd-win
    $cwd = Get-Location
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -cwd `"$cwd`"" -Verb RunAs -Wait
    exit
} else {
    Write-Output "usbipd is already installed."
}
# Check that WSL2 is installed, if not, install WSL2
if (-not (Get-WindowsOptionalFeature -FeatureName Microsoft-Windows-Subsystem-Linux -Online -ErrorAction SilentlyContinue)) {
    Write-Output "WSL2 is not installed. Installing WSL2..."
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    $cwd = Get-Location
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -cwd `"$cwd`"" -Verb RunAs -Wait
    exit
} else {
    Write-Output "WSL2 is already installed."
}
# Get a list of all USB devices and filter by those containing 'COM' in the device name
$usbDevices = usbipd list | Where-Object { $_ -match 'COM' }

# Write the number of USB devices found
Write-Host "USB devices found in usbdevices: $($usbDevices)"

# Extract the BUSID of each filtered device and store in an array
foreach ($device in $usbDevices) {
    $usbDeviceArray = $device -split '  ' | Where-Object { $_ -ne '' }
    $busId = $usbDeviceArray[0]
    $state = $usbDeviceArray[3]
    if ($state -eq 'Not shared') {
        usbipd bind --busid $busId
    }
    if ($state -ne 'Attached') {
        usbipd attach --wsl --busid $busId
        Write-Host "Attached USB device with BUSID: $busId"
    }
    else {
        Write-Host "USB device with BUSID: $busId is already attached"
    }
}

# Build the Docker image
docker build `-t "qview3d/ubuntu:24.04" ` -f ".docker/Dockerfile" .

Read-Host -Prompt "Press Enter to exit"
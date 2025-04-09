import platform
import subprocess

def run_script():
    system = platform.system()

    if system == "Windows":
        commands ={
            "docker-build.ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File", "docker-build.ps1"],
            "docker-run.ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File", "docker-run.ps1"]
        }
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        commands = {
            "docker-run.sh": ["bash", "docker-run.sh"] # the bash script builds and runs in the same script for Linux and macOS
        }
    else:
        print(f"Unsupported OS: {system}")
        return

    for script, command in commands.items():
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")

if __name__ == "__main__":
    run_script()

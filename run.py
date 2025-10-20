#!/usr/bin/env python3.12
import platform
import subprocess
import os

# NPM and Python3 with venv and pip must be installed to use this script

"""
QView3D Application Launcher
============================

Architecture:
- Middleware (port 3500) is ALWAYS running - it's the permanent communication layer
- Frontend ALWAYS connects to middleware (port 3500)
- Middleware routes requests to the appropriate backend (Python or JavaScript)
- Clear your browser's localStorage if you encounter port issues:
  1. Open browser console (F12)
  2. Run: localStorage.clear()
  3. Refresh the page

Backend Modes:
- python: Python Flask backend (port 8000) - DEFAULT
- javascript: Node.js backend (port 3000) - Serial communication focus

The middleware automatically routes requests and provides fallback between backends.
"""

# TODO Allow a .env file to overwrite the below configurations
# Relative locations of the client and server directories from the root directory
CLIENT_LOCAL_PATH = "client"
SERVER_LOCAL_PATH = "server-python"
JS_SERVER_LOCAL_PATH = "server-javascript"
MIDDLEWARE_LOCAL_PATH = "middleware"

# The name of the database file
DATABASE_FILE_NAME="QView.db"

# If the database file should be deleted before running the server, then set this to true
START_FROM_NEW_DATABASE = True

# Server configuration
FLASK_SERVER_IP = "localhost" # TODO Have this affect the server
FLASK_SERVER_PORT = 8000 # TODO Have this affect the server
FLASK_SERVER_WEB_SOCKET_PORT = 8001 # TODO Have this affect the server

# JavaScript Server configuration
JS_SERVER_PORT = 3000
JS_SERVER_WS_PORT = 3001

# Backend selection: "python" or "javascript"
# - python: Use Python Flask backend only (default)
# - javascript: Use Node.js backend only
BACKEND_MODE = "python"  # Default to python backend

# Client configuration
VITE_CLIENT_IP = "SAME_AS_SERVER"
VITE_CLIENT_PORT = 8002
VITE_LOG_LEVEL = "error"

# Checks to make sure the script is being run in the root directory of the project (it assumes this by default)
if not (os.path.exists(CLIENT_LOCAL_PATH) and os.path.exists(SERVER_LOCAL_PATH)):
    raise Exception("Please run this script in the root directory of the project")

# TODO Enforce Python version (Lock to 3.12)

def build_client():
    # Build the client for production
    print("Building client...")
    result = subprocess.run(
        "npm run build-only",
        shell=True,
        cwd=CLIENT_LOCAL_PATH
    )
    if result.returncode == 0:
        print("Client build complete")
    else:
        print("Client build failed, but continuing...")

def start_client():
    global VITE_CLIENT_IP
    if VITE_CLIENT_IP == "SAME_AS_SERVER":
        VITE_CLIENT_IP = FLASK_SERVER_IP

    # Start the client in the background
    return subprocess.Popen(
        # Command for the client
        f"npx vite --port {VITE_CLIENT_PORT} --host {VITE_CLIENT_IP} --cors true --logLevel {VITE_LOG_LEVEL}",
        shell=True,
        # The working directory for the command
        cwd=CLIENT_LOCAL_PATH
    )

def start_server(fresh_database):
    # Delete the database file if the developer wants a fresh database for the server
    if fresh_database == True:
        # Ensure the database file actually exists
        database_file_path = os.path.join(SERVER_LOCAL_PATH, DATABASE_FILE_NAME)
        if (os.path.exists(database_file_path)):
            try:
                os.remove(database_file_path)
                print("Deleted the database file")
            except OSError as ose:
                print(ose)

    # Start the server in the background using virtual environment
    if current_os == "WINDOWS":
        venv_python = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "Scripts", "python.exe"))
        if os.path.exists(venv_python):
            return subprocess.Popen(
                [venv_python, "app.py"],
                cwd=os.path.abspath(SERVER_LOCAL_PATH)
            )
        else:
            return subprocess.Popen(
                ["py", "app.py"],
                cwd=os.path.abspath(SERVER_LOCAL_PATH)
            )
    else:
        # On Linux/Mac, use .venv (the one we created in WSL)
        venv_python = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".venv", "bin", "python"))
        if os.path.exists(venv_python):
            return subprocess.Popen(
                [venv_python, "app.py"],
                cwd=os.path.abspath(SERVER_LOCAL_PATH)
            )
        else:
            return subprocess.Popen(
                ["python3", "app.py"],
                cwd=os.path.abspath(SERVER_LOCAL_PATH)
            )

def start_js_server():
    # Start the JavaScript server in the background
    return subprocess.Popen(
        "node src/index.js",
        shell=True,
        cwd=JS_SERVER_LOCAL_PATH
    )

def start_middleware():
    # Start the middleware in the background
    # Middleware is ALWAYS running - it's the permanent communication layer
    return subprocess.Popen(
        "node src/index.js",
        shell=True,
        cwd=MIDDLEWARE_LOCAL_PATH
    )


def update_config_json():
    # Update the config.json file with backend settings
    import json
    config_path = os.path.join(SERVER_LOCAL_PATH, "config", "config.json")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Add backend configuration
    config['backends'] = {
        "python": {
            "url": f"http://{FLASK_SERVER_IP}:{FLASK_SERVER_PORT}",
            "ws_port": FLASK_SERVER_WEB_SOCKET_PORT
        },
        "javascript": {
            "url": f"http://localhost:{JS_SERVER_PORT}",
            "ws_port": JS_SERVER_WS_PORT
        }
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"Updated config.json with backend mode: {BACKEND_MODE}")

def install_software(current_os: str):
    # Setup virtual environment
    # subprocess.run waits for the process to end before continuing the script
    # this is why it's being used instead of Popen
    if current_os == "LINUX/MAC":
        subprocess.run(
            ["python3.12", "-m", "venv", os.path.join(SERVER_LOCAL_PATH, ".python-venv")]
        )
    elif current_os == "WINDOWS":
        subprocess.run(
            ["py", "-3.12", "-m", "venv", os.path.join(SERVER_LOCAL_PATH, ".python-venv")]
        )
    else:
        raise Exception("What OS are you using?")

    # Install server dependencies
    if current_os == "WINDOWS":
        # On Windows, use Scripts directory and the virtual environment's pip
        venv_pip = os.path.join(SERVER_LOCAL_PATH, ".python-venv", "Scripts", "pip.exe")
        if os.path.exists(venv_pip):
            try:
                subprocess.run(
                    [venv_pip, "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error installing Python dependencies: {e}")
                print("Trying with system pip...")
                subprocess.run(
                    ["pip", "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                    check=True
                )
        else:
            print("Virtual environment pip not found, using system pip...")
            subprocess.run(
                ["pip", "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                check=True
            )
    else:
        # On Linux/Mac, use bin directory
        venv_pip = os.path.join(SERVER_LOCAL_PATH, ".python-venv", "bin", "pip")
        if os.path.exists(venv_pip):
            try:
                subprocess.run(
                    [venv_pip, "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error installing Python dependencies: {e}")
                print("Trying with system pip...")
                subprocess.run(
                    ["pip3", "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                    check=True
                )
        else:
            print("Virtual environment pip not found, using system pip...")
            subprocess.run(
                ["pip3", "install", "-r", os.path.join(SERVER_LOCAL_PATH, "dependencies.txt")],
                check=True
            )

    # Install client dependencies
    subprocess.run(
        "npm i",
        shell=True,
        # Set the working directory for the process to the client folder
        cwd=CLIENT_LOCAL_PATH
    )

    # Install JavaScript server dependencies
    subprocess.run(
        "npm i",
        shell=True,
        cwd=JS_SERVER_LOCAL_PATH
    )

    # Install middleware dependencies
    subprocess.run(
        "npm i",
        shell=True,
        cwd=MIDDLEWARE_LOCAL_PATH
    )

    print("Install complete")


def get_user_configuration():
    # .upper() ensures that lower case letters are fine as well
    user_configuration = input("Would like to: Install Dependencies[I], Run the program in debug mode[D](The default), Run the program in release mode[R], and Cancel[C] ").upper()

    # Ensure the user input is correct
    match user_configuration:
        case "I" | "D" | "R" | "C": # Return the configuration
            return user_configuration
        case "": # Handle the default case
            return "D"
        case _:
            print("Not a valid configuration")
            # Continue the loop if the user puts the wrong input
            return get_user_configuration()
        
def start_debug(fresh_database):
    # Update config.json with current backend mode
    update_config_json()

    # Build client before starting services
    build_client()

    # Start ALL services - middleware handles routing
    processes = []

    print("\n" + "="*60)
    print("Starting QView3D with BOTH Backends")
    print("="*60)
    print(f"Frontend: http://{VITE_CLIENT_IP}:{VITE_CLIENT_PORT}")
    print(f"Middleware: http://localhost:3500 (Redundant Fallback)")
    print(f"Python Backend: http://{FLASK_SERVER_IP}:{FLASK_SERVER_PORT}")
    print(f"JavaScript Backend: http://localhost:{JS_SERVER_PORT}")
    print(f"Default Backend: {BACKEND_MODE}")
    print("-"*60)

    # Start middleware first (handles routing and fallback)
    processes.append(start_middleware())

    # Start both backends for redundancy
    processes.append(start_server(fresh_database))
    processes.append(start_js_server())

    # Start client
    processes.append(start_client())

    return processes


running_processes = []
is_installing = False

# Get the user configuration
user_configuration = get_user_configuration()

# Get the current OS being used
current_os = platform.system()

# Map platform system to our OS strings
if current_os == "Windows":
    current_os = "WINDOWS"
elif current_os in ["Linux", "Darwin"]:
    current_os = "LINUX/MAC"

match user_configuration:
    case "I":
        is_installing = True
        install_software(current_os)
    case "D":
        running_processes = start_debug(START_FROM_NEW_DATABASE)
    case "R":
        print("Doesn't do anything yet")
        pass # TODO Add release mode
    case "C":
        print("Process canceled")
        exit(0)

# Added to prevent the script from terminating until the user manually closes it
# If the user chooses to install software, then the loop will not start
try:
    while not is_installing:
        try:
            input() # Stop the loop from running indefinitely
        except EOFError:
            # Handle EOF when running in non-interactive mode (like WSL)
            print("Running in non-interactive mode. Services started.")
            # Keep the processes running by waiting
            import time
            while True:
                time.sleep(1)
except KeyboardInterrupt: # Loop will close when a KeyboardInterrupt exception is thrown
    # Terminate the background processes
    for process in running_processes:
        if process is not None:
            process.terminate()
    print("All processes terminated")
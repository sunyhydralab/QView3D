#!/usr/bin/env python3.12
import platform
import subprocess
import os

# NPM and Python3 with venv and pip must be installed to use this script

"""
QView3D Application Launcher
============================

Architecture:
- Browser connects to MIDDLEWARE on port 8002
- Middleware proxies requests to selected backend (Python 8000 or JavaScript 8005)
- Python emulator runs on port 8004 (if using Python backend)
- Clear your browser's localStorage if you encounter port issues:
  1. Open browser console (F12)
  2. Run: localStorage.clear()
  3. Refresh the page

Backend Modes:
- python: Python Flask backend (port 8000) + Emulator (port 8004) - DEFAULT
- javascript: Node.js backend (port 8005) + Emulator (port 8007)

User accesses app at: http://localhost:8002 (middleware)
"""

# TODO Allow a .env file to overwrite the below configurations
# Relative locations of the client and server directories from the root directory
CLIENT_LOCAL_PATH = "client"
SERVER_LOCAL_PATH = "server-python"
JS_SERVER_LOCAL_PATH = "server-javascript"
MIDDLEWARE_LOCAL_PATH = "middleware"

# The name of the database file
DATABASE_FILE_NAME="QView.db"

# Database is ALWAYS wiped on startup for clean state
START_FROM_NEW_DATABASE = True  # Always True - ensures fresh database every run

# Middleware configuration
MIDDLEWARE_PORT = 8002

# Python Server configuration
FLASK_SERVER_IP = "localhost"
FLASK_SERVER_PORT = 8000
PYTHON_EMULATOR_PORT = 8004

# JavaScript Server configuration
JS_SERVER_PORT = 8005
JS_EMULATOR_PORT = 8007

# Backend selection: "python" or "javascript"
# - python: Use Python Flask backend + Python emulator (default)
# - javascript: Use Node.js backend + JavaScript emulator
BACKEND_MODE = "python"  # Default to Python backend

# Client configuration (for development mode)
VITE_CLIENT_IP = "SAME_AS_SERVER"
VITE_CLIENT_PORT = 5173  # Default Vite dev server port
VITE_LOG_LEVEL = "error"

# Checks to make sure the script is being run in the root directory of the project (it assumes this by default)
if not (os.path.exists(CLIENT_LOCAL_PATH) and os.path.exists(SERVER_LOCAL_PATH)):
    raise Exception("Please run this script in the root directory of the project")

# TODO Enforce Python version (Lock to 3.12)

def build_client():
    # Build the client for production (ALWAYS runs for fresh build)
    print("\n" + "="*60)
    print("REBUILDING CLIENT...")
    print("="*60)
    result = subprocess.run(
        "npm run build-only",
        shell=True,
        cwd=CLIENT_LOCAL_PATH
    )
    if result.returncode == 0:
        print("Client build complete")
    else:
        print("Client build failed, but continuing...")
    print("="*60 + "\n")

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
    # ALWAYS delete the database file for a fresh start
    database_file_path = os.path.join(SERVER_LOCAL_PATH, DATABASE_FILE_NAME)
    if (os.path.exists(database_file_path)):
        try:
            os.remove(database_file_path)
            print("Database wiped - starting fresh")
        except OSError as ose:
            print(f"Failed to delete database: {ose}")
    else:
        print("No existing database found - starting fresh")

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
        # On Linux/Mac, use .python-venv (the one we created in WSL)
        venv_python = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "bin", "python"))
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
    env = os.environ.copy()
    env['PORT'] = str(JS_SERVER_PORT)
    return subprocess.Popen(
        "node src/index.js",
        shell=True,
        cwd=JS_SERVER_LOCAL_PATH,
        env=env
    )

def start_middleware():
    # Start the middleware server in the background
    print(f"Starting middleware on port {MIDDLEWARE_PORT}...")
    return subprocess.Popen(
        "node src/index.js",
        shell=True,
        cwd=MIDDLEWARE_LOCAL_PATH
    )

def start_emulator():
    # Start the Python emulator server in the background
    emulator_port = PYTHON_EMULATOR_PORT if BACKEND_MODE == "python" else JS_EMULATOR_PORT
    print(f"Starting {BACKEND_MODE} emulator on port {emulator_port}...")

    if BACKEND_MODE == "python":
        # Start Python emulator
        if current_os == "WINDOWS":
            venv_python = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "Scripts", "python.exe"))
            if os.path.exists(venv_python):
                return subprocess.Popen(
                    [venv_python, "-m", "emulator.emulator_server"],
                    cwd=os.path.abspath(SERVER_LOCAL_PATH)
                )
            else:
                return subprocess.Popen(
                    ["py", "-m", "emulator.emulator_server"],
                    cwd=os.path.abspath(SERVER_LOCAL_PATH)
                )
        else:
            # On Linux/Mac, use .python-venv
            venv_python = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "bin", "python"))
            if os.path.exists(venv_python):
                return subprocess.Popen(
                    [venv_python, "-m", "emulator.emulator_server"],
                    cwd=os.path.abspath(SERVER_LOCAL_PATH)
                )
            else:
                return subprocess.Popen(
                    ["python3", "-m", "emulator.emulator_server"],
                    cwd=os.path.abspath(SERVER_LOCAL_PATH)
                )
    else:
        # JavaScript emulator would go here (not implemented yet)
        print("JavaScript emulator not yet implemented")
        return None

def update_config_json():
    # Update the config.json file with backend settings
    import json
    config_path = os.path.join(SERVER_LOCAL_PATH, "config", "config.json")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Add middleware configuration
    config['middleware'] = {
        "port": MIDDLEWARE_PORT,
        "mode": BACKEND_MODE
    }

    # Add backend configuration
    config['backends'] = {
        "python": {
            "url": f"http://{FLASK_SERVER_IP}:{FLASK_SERVER_PORT}",
            "port": FLASK_SERVER_PORT,
            "ws_port": FLASK_SERVER_PORT,  # SocketIO on same port
            "emulator_port": PYTHON_EMULATOR_PORT
        },
        "javascript": {
            "url": f"http://localhost:{JS_SERVER_PORT}",
            "port": JS_SERVER_PORT,
            "ws_port": JS_SERVER_PORT,  # SocketIO on same port
            "emulator_port": JS_EMULATOR_PORT
        }
    }

    # Set active backend mode
    config['active_backend'] = BACKEND_MODE

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
    """
    Get user configuration for install/run mode
    Returns: (mode, backend) tuple
    """
    # .upper() ensures that lower case letters are fine as well
    user_mode = input("Would like to: Install Dependencies[I], Run the program in debug mode[D](The default), Run the program in release mode[R], and Cancel[C] ").upper()

    # Ensure the user input is correct
    match user_mode:
        case "I":
            return ("I", None)  # No backend needed for install
        case "C":
            return ("C", None)  # No backend needed for cancel
        case "D" | "R" | "":
            # Ask for backend selection
            if user_mode == "":
                user_mode = "D"  # Default to debug mode

            backend_choice = input("Select Backend: [P]ython (default), [J]avaScript ").upper()

            match backend_choice:
                case "P":
                    return (user_mode, "python")
                case "J":
                    return (user_mode, "javascript")
                case "":  # Default to Python
                    return (user_mode, "python")
                case _:
                    print("Not a valid backend choice")
                    return get_user_configuration()
        case _:
            print("Not a valid configuration")
            # Continue the loop if the user puts the wrong input
            return get_user_configuration()
        
def start_debug(fresh_database):
    # Update config.json with current backend mode
    update_config_json()

    # Skip client build - using Vite dev server for hot reload development
    # build_client()

    # Start all services
    processes = []

    print("\n" + "="*60)
    print(f"STARTING QView3D - {BACKEND_MODE.upper()} BACKEND + MIDDLEWARE")
    print("="*60)
    print(f"User Access: http://localhost:{MIDDLEWARE_PORT}")
    print(f"Middleware:  http://localhost:{MIDDLEWARE_PORT}")

    if BACKEND_MODE == "python":
        print(f"Backend:     http://{FLASK_SERVER_IP}:{FLASK_SERVER_PORT}")
        print(f"Emulator:    http://localhost:{PYTHON_EMULATOR_PORT}")
    elif BACKEND_MODE == "javascript":
        print(f"Backend:     http://localhost:{JS_SERVER_PORT}")
        print(f"Emulator:    Port {JS_EMULATOR_PORT} (not implemented)")

    print(f"Vite Dev:    http://localhost:{VITE_CLIENT_PORT} (hot reload enabled)")
    print("-"*60)
    print("NOTE: Database is wiped on every startup")
    print("NOTE: Using Vite dev server for dynamic development (no build step)")
    print("NOTE: Access the app at http://localhost:8002")
    print("-"*60)

    # Start the selected backend
    if BACKEND_MODE == "python":
        processes.append(start_server(fresh_database))
    elif BACKEND_MODE == "javascript":
        processes.append(start_js_server())
    else:
        print(f"Warning: Unknown backend mode '{BACKEND_MODE}', starting Python backend")
        processes.append(start_server(fresh_database))

    # Start emulator
    emulator_process = start_emulator()
    if emulator_process:
        processes.append(emulator_process)

    # Start middleware
    processes.append(start_middleware())

    # Start client (Vite dev server for development)
    processes.append(start_client())

    return processes


running_processes = []
is_installing = False

# Get the user configuration
user_mode, selected_backend = get_user_configuration()

# Update BACKEND_MODE based on user selection
if selected_backend:
    BACKEND_MODE = selected_backend

# Get the current OS being used
current_os = platform.system()

# Map platform system to our OS strings
if current_os == "Windows":
    current_os = "WINDOWS"
elif current_os in ["Linux", "Darwin"]:
    current_os = "LINUX/MAC"

match user_mode:
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
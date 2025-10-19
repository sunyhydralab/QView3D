#!/usr/bin/env python3.12
import platform
import subprocess
import os

# NPM and Python3 with venv and pip must be installed to use this script

# TODO Allow a .env file to overwrite the below configurations
# Relative locations of the client and server directories from the root directory
CLIENT_LOCAL_PATH = "client"
SERVER_LOCAL_PATH = "server-python"
MIDDLEWARE_LOCAL_PATH = "middleware"
JS_SERVER_LOCAL_PATH = "server-javascript"

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

# Middleware configuration
MIDDLEWARE_PORT = 3500
MIDDLEWARE_WS_PORT = 3501

# Backend selection: "python", "javascript", "hybrid"
# - python: Use Python Flask backend only
# - javascript: Use Node.js backend only
# - hybrid: Run both backends with middleware for automatic fallback
BACKEND_MODE = "hybrid"  # Default to hybrid mode for redundancy

# Client configuration
VITE_CLIENT_IP = "SAME_AS_SERVER"
VITE_CLIENT_PORT = 8002
VITE_LOG_LEVEL = "error"

# Checks to make sure the script is being run in the root directory of the project (it assumes this by default)
if not (os.path.exists(CLIENT_LOCAL_PATH) and os.path.exists(SERVER_LOCAL_PATH)):
    raise Exception("Please run this script in the root directory of the project")

# TODO Enforce Python version (Lock to 3.12)

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

    # Start the server in the background
    if current_os == "WINDOWS":
        # On Windows, use Scripts directory
        venv_flask = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "Scripts", "flask.exe"))
        return subprocess.Popen(
            [venv_flask, 'run'],
            cwd=os.path.abspath(SERVER_LOCAL_PATH)
        )
    else:
        # On Linux/Mac, use bin directory
        venv_flask = os.path.abspath(os.path.join(SERVER_LOCAL_PATH, ".python-venv", "bin", "flask"))
        return subprocess.Popen(
            [venv_flask, 'run'],
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
    # Start the middleware service in the background
    return subprocess.Popen(
        "node src/index.js",
        shell=True,
        cwd=MIDDLEWARE_LOCAL_PATH
    )

def update_config_json():
    # Update the config.json file with middleware settings
    import json
    config_path = os.path.join(SERVER_LOCAL_PATH, "config", "config.json")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Add middleware configuration
    config['middleware'] = {
        "mode": BACKEND_MODE,
        "port": MIDDLEWARE_PORT,
        "ws_port": MIDDLEWARE_WS_PORT
    }

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
        # On Linux/Mac, use bin directory
        venv_pip = os.path.join(SERVER_LOCAL_PATH, ".python-venv", "bin", "pip")
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

    # Install client dependencies
    subprocess.run(
        "npm i",
        shell=True,
        # Set the working directory for the process to the client folder
        cwd=CLIENT_LOCAL_PATH
    )

    # Install middleware dependencies
    subprocess.run(
        "npm i",
        shell=True,
        cwd=MIDDLEWARE_LOCAL_PATH
    )

    # Install JavaScript server dependencies
    subprocess.run(
        "npm i",
        shell=True,
        cwd=JS_SERVER_LOCAL_PATH
    )

    print("Install complete")

def get_backend_selection():
    global BACKEND_MODE
    print("\nSelect Backend Mode:")
    print("  1. Python Backend (default, full-featured)")
    print("  2. JavaScript Backend (serial communication focus)")
    print("  3. Hybrid Mode (run both backends simultaneously)")

    selection = input("Enter selection [1-3] (default: 1): ").strip()

    match selection:
        case "1" | "":
            BACKEND_MODE = "python"
        case "2":
            BACKEND_MODE = "javascript"
        case "3":
            BACKEND_MODE = "hybrid"
        case _:
            print("Invalid selection, using Python backend")
            BACKEND_MODE = "python"

    print(f"Backend mode set to: {BACKEND_MODE}")
    return BACKEND_MODE

def get_user_configuration():
    # .upper() ensures that lower case letters are fine as well
    user_configuration = input("Would like to: Install Dependencies[I], Run the program in debug mode[D](The default), Run the program in release mode[R], Select Backend[B], and Cancel[C] ").upper()

    # Ensure the user input is correct
    match user_configuration:
        case "I" | "D" | "R" | "B" | "C": # Return the configuration
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

    # Start services based on backend mode
    processes = []

    if BACKEND_MODE == "python":
        # Python only mode
        processes.append(start_client())
        processes.append(start_server(fresh_database))
    elif BACKEND_MODE == "javascript":
        # JavaScript only mode
        processes.append(start_client())
        processes.append(start_js_server())
    elif BACKEND_MODE == "hybrid":
        # Hybrid mode: start both backends and middleware
        processes.append(start_client())
        processes.append(start_server(fresh_database))
        processes.append(start_js_server())
        processes.append(start_middleware())

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
    case "B":
        get_backend_selection()
        running_processes = start_debug(START_FROM_NEW_DATABASE)
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
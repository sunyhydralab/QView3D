#!/usr/bin/env python3.12
import platform
import subprocess
import os

# NPM and Python3 with venv and pip must be installed to use this script

# TODO Allow a .env file to overwrite the below configurations
# Relative locations of the client and server directories from the root directory
CLIENT_LOCAL_PATH = "client"
SERVER_LOCAL_PATH = "server"

# The name of the database file
DATABASE_FILE_NAME="hvamc.db"

# If the database file should be deleted before running the server, then set this to true
START_FROM_NEW_DATABASE = True

# Server configuration
FLASK_SERVER_IP = "localhost" # TODO Have this affect the server
FLASK_SERVER_PORT = 8000 # TODO Have this affect the server
FLASK_SERVER_WEB_SOCKET_PORT = 8001 # TODO Have this affect the server

# Client configuration
VITE_CLIENT_IP = "SAME_AS_SERVER"
VITE_CLIENT_PORT = 8002
VITE_LOG_LEVEL = "info"

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
        ["npx", "vite", "--port", str(VITE_CLIENT_PORT), "--host", VITE_CLIENT_IP, "--cors", "true", "--logLevel", VITE_LOG_LEVEL],
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
    return subprocess.Popen(
        # Command for the server
        ['flask', 'run'],
        # The working directory for the command
        cwd=SERVER_LOCAL_PATH,
        # Enable the Python virtual environment
        env={"PATH": os.path.join(".", ".python-venv", "bin")}
    )

def install_software(current_os: str):
    # Setup virtual environment
    # subprocess.run waits for the process to end before continuing the script
    # this is why it's being used instead of Popen
    if current_os == "LINUX/MAC":
        subprocess.run(
            ["python3.12", "-m", "venv", os.path.join("server", ".python-venv")]
        )
    elif current_os == "WINDOWS":
        subprocess.run(
            ["py", "-3.12", "-m", "venv", os.path.join("server", ".python-venv")]
        )
    else:
        raise Exception("What OS are you using?")

    # Install server dependencies
    subprocess.run(
        ["pip", "install", "-r", os.path.join("server", "dependencies.txt")],
        # Enable the Python virtual environment
        env={"PATH": os.path.join(".", "server", ".python-venv", "bin")}
    )

    # Install client dependencies
    subprocess.run(
        ["npm", "i"],
        # Set the working directory for the process to the client folder
        cwd=CLIENT_LOCAL_PATH
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
    return start_client(), start_server(fresh_database)


flask_process = None
vite_process = None
is_installing = False

# Get the user configuration
user_configuration = get_user_configuration()

# Get the current OS being used
current_os = platform.system()

match user_configuration:
    case "I":
        is_installing = True
        if current_os == "Windows":
            install_software("WINDOWS")
        elif current_os in ["Linux", "Darwin"]:
            install_software("LINUX/MAC")
    case "D":
        vite_process, flask_process = start_debug(START_FROM_NEW_DATABASE)
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
        input() # Stop the loop from running indefinitely
except KeyboardInterrupt: # Loop will close when a KeyboardInterrupt exception is thrown
    # Terminate the background processes
    flask_process.terminate()
    vite_process.terminate()
    print("Flask and Vite terminated")
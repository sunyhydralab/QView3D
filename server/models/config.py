import json
import os

def base_url():
    return f"http://{ip}:{port}"

# load config file
def load_config(file_path):
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

configFileLoc = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json'))
config = load_config(configFileLoc)
environment = config.get('environment', 'development')
ip = config.get('ip', '127.0.0.1')
database_uri = config.get('databaseURI', 'hvamc') + ".db"
port = os.environ.get('FLASK_RUN_PORT', 8000)

Config = {
    'base_url': base_url(),
    'environment': environment,
    'ip': ip,
    'database_uri': database_uri,
    'port': port
}
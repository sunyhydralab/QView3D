import json
import os

def base_url():
    return f"http://{ip}:{port}"

# load config file
def load_config(file_path):
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

config = load_config('./config/config.json')
environment = config.get('environment', 'development')
ip = config.get('ip', '127.0.0.1')
database_uri = config.get('databaseURI', 'hvamc') + ".db"
port = os.environ.get('FLASK_RUN_PORT', 8000)

discord_config = config.get('discord', {})
discord_enabled = discord_config.get('enabled', False)
discord_token = discord_config.get('token', None)
discord_prefix = discord_config.get('command_prefix', '!')
discord_issues_channel = discord_config.get('issues_channel', None)

Config = {
    'base_url': base_url(),
    'environment': environment,
    'ip': ip,
    'database_uri': database_uri,
    'port': port,
    'discord_enabled': discord_enabled,
    'discord_token': discord_token,
    'command_prefix': discord_prefix,
    'discord_issues_channel': discord_issues_channel
}
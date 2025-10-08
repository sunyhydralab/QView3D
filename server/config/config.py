import json
import os

def base_url():
    return f"http://{server_ip}:{server_port}"

# load config file
def load_config(file_path):
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

configFileLoc = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json'))
config = load_config(configFileLoc)
environment = config.get('environment', 'development')

# Server configuration
server_config = config.get('server', {})
server_ip = server_config.get('ip', 'localhost')
server_port = server_config.get('port', 8000)
websocket_port = server_config.get('websocket_port', 8001)

# Client configuration
client_config = config.get('client', {})
client_ip = client_config.get('ip', 'SAME_AS_SERVER')
client_port = client_config.get('port', 8002)
client_log_level = client_config.get('log_level', 'error')

# Database configuration
database_config = config.get('database', {})
database_file_name = database_config.get('file_name', 'QView.db')
database_start_from_new = database_config.get('start_from_new', True)
database_uri = config.get('databaseURI', 'QView') + ".db"

# Discord configuration
discord_config = config.get('discord', {})
discord_enabled = discord_config.get('enabled', False)
discord_token = discord_config.get('token', None)
discord_prefix = discord_config.get('command_prefix', '!')
discord_issues_channel = discord_config.get('issues_channel', None)
discord_issues_role = discord_config.get('issues_role', None)

# Queue configuration
queue = config.get('queue', {})

Config = {
    'base_url': base_url(),
    'environment': environment,
    # Server settings
    'server_ip': server_ip,
    'server_port': server_port,
    'websocket_port': websocket_port,
    # Client settings
    'client_ip': client_ip,
    'client_port': client_port,
    'client_log_level': client_log_level,
    # Database settings
    'database_uri': database_uri,
    'database_file_name': database_file_name,
    'database_start_from_new': database_start_from_new,
    # Queue settings
    'queue_auto_progress': queue.get('auto_progress', True),
    'queue_auto_progress_delay': queue.get('auto_progress_delay', 2),
    # Discord settings
    'discord_enabled': discord_enabled,
    'discord_token': discord_token,
    'command_prefix': discord_prefix,
    'discord_issues_channel': discord_issues_channel,
    'discord_issues_role': discord_issues_role
}
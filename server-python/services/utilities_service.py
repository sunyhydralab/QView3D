import subprocess

class UtilitiesService:
    def __init__(self, app):
        self.app = app

    def get_emu_ports(self):
        fake_device = next(iter(self.app.emulator_connections.values()), None)
        if fake_device and hasattr(fake_device, 'fake_port'):
            return [fake_device.fake_port, fake_device.fake_name, fake_device.fake_hwid]
        return [None, None, None]

    def run_go_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            from services.error_service import ErrorService
            ErrorService.handle_errors_and_logging(e)
            return None
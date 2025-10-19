import subprocess

class CLIService:
    def __init__(self, app):
        self.app = app
        self.setup_cli_commands()
    
    def setup_cli_commands(self):
        """Setup Flask CLI commands."""
        @self.app.cli.command("test")
        def run_tests():
            """Run all tests."""
            subprocess.run(["python", "../Tests/parallel_test_runner.py"])
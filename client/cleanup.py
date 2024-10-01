import os
import shutil

# Define the path to the 'out' directory
out_dir = 'out/QView3D-win32-x64/resources/app'
node_modules_dir = os.path.join(out_dir, 'node_modules')
electron_squirrel_startup_dir = os.path.join(node_modules_dir, 'electron-squirrel-startup')
temp_electron_squirrel_startup_dir = os.path.join(out_dir, 'electron-squirrel-startup')

# List of unnecessary files and directories to delete
unnecessary_files = [
    'node_modules',
    'src',
    'tests',
    '.git',
    '.gitignore',
    'README.md',
    'package-lock.json',
    'yarn.lock',
    'webpack.config.js',
    'tsconfig.json',
    'jest.config.js',
    'babel.config.js',
    '.eslintrc.js',
    '.prettierrc.json',
    '.vscode',
    '.env',
    'docs',
    'examples',
    'scripts',
    'coverage',
    'public',
    'build',
    'logs',
    'tmp',
    'temp',
    'tsconfig.app.json',
    'tsconfig.node.json',
    'tsconfig.vitest.json',
    'Installer.nsi',
    'Combo Installer.nsi',
    'tsconfig.app.tsbuildinfo',
    'tsconfig.node.tsbuildinfo',
    'tsconfig.vitest.tsbuildinfo',
    'vite.config.ts',
    'vitest.config.ts',
    'env.d.ts',
    'QView3D Setup.exe',
    'index.html',
    '.eslintrc.cjs'
    'cleanup.py'
]

def move_electron_squirrel_startup_to_app():
    if os.path.exists(electron_squirrel_startup_dir):
        shutil.move(electron_squirrel_startup_dir, temp_electron_squirrel_startup_dir)
        print(f"Moved {electron_squirrel_startup_dir} to {temp_electron_squirrel_startup_dir}")

def move_electron_squirrel_startup_back():
    if os.path.exists(temp_electron_squirrel_startup_dir):
        os.makedirs(node_modules_dir, exist_ok=True)
        shutil.move(temp_electron_squirrel_startup_dir, electron_squirrel_startup_dir)
        print(f"Moved {temp_electron_squirrel_startup_dir} back to {electron_squirrel_startup_dir}")

def delete_unnecessary_files(directory, files_to_delete):
    for item in files_to_delete:
        item_path = os.path.join(directory, item)
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Deleted directory: {item_path}")
            else:
                os.remove(item_path)
                print(f"Deleted file: {item_path}")

if __name__ == "__main__":
    move_electron_squirrel_startup_to_app()
    delete_unnecessary_files(out_dir, unnecessary_files)
    move_electron_squirrel_startup_back()
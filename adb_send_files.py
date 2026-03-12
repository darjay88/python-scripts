import os
import sys
import subprocess
from pathlib import Path

def send_file_via_adb(file_path, device_id):
    try:
        # Constructing adb push command
        command = ['adb', 'push', str(file_path), f'/data/local/tmp/{file_path.name}']
        print(f'Sending {file_path} to Android device {device_id}...')
        # Executing the command
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                print(output.strip().decode('utf-8'))
        return_code = process.wait()
        if return_code == 0:
            print(f'Successfully sent {file_path.name} to {device_id}.')
        else:
            print(f'Error sending {file_path.name}: {process.stderr.read().decode()}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

def send_directory_via_adb(directory_path, device_id):
    try:
        for file_path in Path(directory_path).rglob('*'):
            if file_path.is_file():
                send_file_via_adb(file_path, device_id)
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python adb_send_files.py <file_or_directory_path> <device_id>')
        sys.exit(1)
    path = sys.argv[1]
    device_id = sys.argv[2]

    if os.path.isfile(path):
        send_file_via_adb(Path(path), device_id)
    elif os.path.isdir(path):
        send_directory_via_adb(Path(path), device_id)
    else:
        print('Provided path is neither a file nor a directory.')

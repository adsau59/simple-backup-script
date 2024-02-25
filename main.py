import json
import os
import py7zr
import paramiko
from datetime import datetime
from stat import S_ISDIR
from pathlib import PurePosixPath

from py7zr import SevenZipFile


def create_7z(service_name, directories, password, backup_location, ssh_keys):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive_name = f"{service_name}_backup_{timestamp}.7z"
    archive_path = os.path.join(backup_location, service_name, archive_name)

    with py7zr.SevenZipFile(archive_path, 'w', password=password, header_encryption=True) as archive:
        for directory in directories:
            if directory.startswith("ssh://"):
                ssh_directory = directory.replace("ssh://", "")
                download_from_ssh(archive, ssh_directory, ssh_keys)
            else:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_name = os.path.relpath(file_path, directory)
                        arcname = os.path.join(os.path.basename(directory), rel_name)
                        archive.write(file_path, arcname=arcname)

        # Create mapping.json inside the archive
        mapping = {os.path.basename(directory): directory for directory in directories}
        mapping_content = json.dumps(mapping, indent=2)
        archive.writestr(mapping_content, "mapping.json")


def download_from_ssh(archive: SevenZipFile, ssh_directory, ssh_keys):
    ssh_url, remote_path = ssh_directory.split("/", 1)
    ssh_url = ssh_url.rstrip('/')

    # Parse username, hostname, and port
    username, _, host = ssh_url.rpartition('@')
    hostname, _, port = host.partition(':')
    port = int(port) if port else 22

    # Establish SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Use specified keyfile if available
    keyfile = ssh_keys.get(hostname, None)
    if keyfile:
        private_key = paramiko.RSAKey(filename=keyfile)
        ssh.connect(hostname, port=port, username=username, pkey=private_key)
    else:
        ssh.connect(hostname, port=port, username=username)

    try:
        with ssh.open_sftp() as sftp:
            for remote_file_path in sftp_walk(sftp, remote_path):
                print(os.path.basename(remote_path))
                arcname = os.path.join(os.path.basename(remote_path), remote_file_path[len(remote_path)+1:])
                print(f"arcname {arcname}")
                with sftp.file(remote_file_path, 'r') as remote_file:
                    archive.writestr(remote_file.read(), arcname)
    finally:
        ssh.close()


def sftp_walk(sftp, path):
    files = []
    for item in sftp.listdir_attr(path):
        if S_ISDIR(item.st_mode):
            print(xjoin(path, item.filename))
            files.extend(sftp_walk(sftp, xjoin(path, item.filename)))
        else:
            files.append(xjoin(path, item.filename))
    return files


def xjoin(*args):
    return str(PurePosixPath(*args))

def main():
    # Load JSON from file
    with open('config.json', 'r') as json_file:
        config = json.load(json_file)

    backup_location = config['backup_location']
    password = config['password']
    services = config['services']
    ssh_keys = config.get('ssh_keys', {})

    for service, directories in services.items():
        service_folder = os.path.join(backup_location, service)
        os.makedirs(service_folder, exist_ok=True)
        create_7z(service, directories, password, backup_location, ssh_keys)


if __name__ == "__main__":
    main()

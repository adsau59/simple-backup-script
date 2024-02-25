# Simple Backup Script

A simple script to backup folders on your system or on a server and create a zip and store it locally

Sample Config
```json
{
  "backup_location": "/path/to/backup",
  "password": "your_password_here",
  "ssh_keys": {
    "hostname1": "/path/to/keyfile1",
    "hostname2": "/path/to/keyfile2"
  },
  "services": {
    "service1": [
      "/path/to/local/directory1",
      "ssh://username@hostname1:22/path/to/remote/directory1"
    ],
    "service2": [
      "/path/to/local/directory2",
      "ssh://username@hostname2:22/path/to/remote/directory2"
    ]
  }
}
```
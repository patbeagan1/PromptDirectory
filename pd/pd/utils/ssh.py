"""SSH-related utilities."""

import os
import subprocess
from pathlib import Path

def setup_ssh_agent():
    """Set up SSH agent and add common SSH keys"""
    # Start SSH agent and capture environment variables
    process = subprocess.Popen(['ssh-agent', '-s'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    output, _ = process.communicate()

    # Parse and set environment variables
    for line in output.splitlines():
        if line.startswith('SSH_AUTH_SOCK=') or line.startswith('SSH_AGENT_PID='):
            var, value = line.split(';', 1)[0].split('=')
            os.environ[var] = value

    # Common SSH key locations and types
    ssh_keys = [Path.home() / ".ssh" / key for key in ["id_ed25519", "id_rsa", "id_ecdsa"]]

    # Try to add each SSH key if it exists
    for key_path in ssh_keys:
        if key_path.is_file():
            print(f"Adding SSH key: {key_path}")
            subprocess.run(['ssh-add', str(key_path)], check=False)

    # Display SSH agent information
    print(f"SSH_AUTH_SOCK: {os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID: {os.environ.get('SSH_AGENT_PID')}")

    # List currently loaded SSH keys
    print("Currently loaded SSH keys:")
    subprocess.run(['ssh-add', '-l'], check=False)



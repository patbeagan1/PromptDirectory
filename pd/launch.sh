#!/usr/bin/env zsh

# Start SSH agent and capture environment variables
eval "$(ssh-agent -s)"

# Common SSH key locations and types
ssh_keys=( ~/.ssh/id_ed25519 ~/.ssh/id_rsa ~/.ssh/id_ecdsa )

# Try to add each SSH key if it exists
for key in "${ssh_keys[@]}"; do
    key_path=$(eval echo "$key")
    if [ -f "$key_path" ]; then
        echo "Adding SSH key: $key_path"
        ssh-add "$key_path"
    fi
done

# Display SSH agent information
echo "SSH_AUTH_SOCK: $SSH_AUTH_SOCK"
echo "SSH_AGENT_PID: $SSH_AGENT_PID"

# List currently loaded SSH keys
echo "Currently loaded SSH keys:"
ssh-add -l

python3 main.py patbeagan1/threeflow-test pbeagan
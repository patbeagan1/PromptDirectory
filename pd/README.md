# Prompt Directory (pd)

A command-line tool for managing and using prompts from a GitHub repository.

## Installation

```bash
uv install pd
```

## Usage

### Configuration

```bash
# Configure pd with your settings
pd --config
```

### Interactive Mode

```bash
# Run with default configuration in interactive mode
pd

# Run with specific repository
pd --repo username/repository

# Run with specific username
pd --username yourname

# Save output to a file
pd --output answer.txt

# Skip SSH agent setup
pd --no-ssh
```

### Command-line Mode

```bash
# List all available snippets
pd list

# Read a snippet
pd read user/snippet

# Write content to a snippet
pd write myuser/snippet --content "Your content here"

# Fork a snippet from another user
pd fork otheruser/snippet

# Edit a snippet in your default editor
pd edit myuser/snippet

# Copy a snippet to clipboard
pd copy user/snippet

# Copy and hydrate a template
pd copy user/template --hydrate --name="John" -- Additional text

# Sync repository with remote
pd sync

# Create a new snippet file
pd new filename

# Direct template hydration
pd template_name --param1="value1" -- Additional text
```

## Configuration

PD stores its configuration in `~/.config/pd/config.json`. You can edit this file directly or use the `--config` flag to update settings interactively.

Main configuration options:

- `prompt_repo`: GitHub repository containing prompts (format: `username/repository`)
- `username`: Your username for the prompt system
- `output_file`: Default file to save answers to

## SSH Keys

Prompt Directory will automatically set up SSH agent and attempt to add common SSH keys when connecting to GitHub. This behavior can be disabled with the `--no-ssh` flag.

## License

MIT
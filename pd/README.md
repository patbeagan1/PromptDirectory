# Prompt Directory (pd)

A command-line tool for managing and using prompts from a GitHub repository.

## Installation

```bash
uv install promptdir
```

## Usage

### Interactive Mode

```bash
# Run with default configuration in interactive mode
promptdir

# Run with specific repository
promptdir --repo username/repository

# Skip SSH agent setup
promptdir --no-ssh
```

### Command-line Mode

```bash
# List all available snippets
promptdir list

# Read a snippet
promptdir read user/snippet

# Write content to a snippet
promptdir write snippet --content "Your content here"

# Fork a snippet from another user
promptdir fork user/snippet

# Edit a snippet in your default editor
promptdir edit snippet

# Copy a snippet to clipboard
promptdir copy user/snippet

# Copy and hydrate a template
promptdir copy user/template --hydrate --name="John" -- Additional text

# Sync repository with remote
promptdir sync

# Create a new snippet file
promptdir new filename

# Direct template hydration
promptdir template_name --param1="value1" -- Additional text
```

## Configuration

PD stores its configuration in `~/.config/pd/config.json`. You can edit this file directly or use the `--config` flag to update settings interactively.

Main configuration options:

- `prompt_repo`: GitHub repository containing prompts (format: `username/repository`)

## SSH Keys

Prompt Directory will automatically set up SSH agent and attempt to add common SSH keys when connecting to GitHub. This behavior can be disabled with the `--no-ssh` flag.

## License

MIT
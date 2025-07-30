#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import textwrap
import traceback
from pathlib import Path

from snippet_repo import SnippetRepo

# Import readline with platform-specific handling
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    try:
        # For Windows, try to use pyreadline or pyreadline3
        try:
            import pyreadline3 as readline
            READLINE_AVAILABLE = True
        except ImportError:
            try:
                import pyreadline as readline
                READLINE_AVAILABLE = True
            except ImportError:
                READLINE_AVAILABLE = False
                print("Warning: readline not available. Command history and completion disabled.")
                print("Install pyreadline3 for Windows or ensure readline is available on Unix systems.")
    except ImportError:
        READLINE_AVAILABLE = False
        print("Warning: readline not available. Command history and completion disabled.")

# Configuration file location
CONFIG_FILE = Path.home() / ".config" / "pd" / "config.json"


def setup_readline(repo):
    """Set up readline for command history and tab completion"""
    if not READLINE_AVAILABLE:
        return

    # Define command completer class
    class CommandCompleter:
        """Tab completion for the REPL."""
        def __init__(self, repo):
            self.repo = repo
            self.commands = [
                "list", "read ", "fork ", "write ", "edit ", "copy ",
                "new ", "sync", "exit", "help", "help "
            ]
            self.command_names = ["list", "read", "fork", "write", "edit", "copy", "new", "sync", "exit", "help"]
            self.current_candidates = []

        def complete(self, text, state):
            """Return the state-th completion for text."""
            if state == 0:  # Generate candidates on first call
                if not text:
                    self.current_candidates = self.commands.copy()
                elif text in ("read ", "fork ", "edit ", "copy "):
                    # Just started a command that needs snippet completion
                    try:
                        snippet_names = self.repo.get_snippet_names() if hasattr(self.repo, 'get_snippet_names') else []
                        self.current_candidates = [text + snippet for snippet in snippet_names]
                    except:
                        print("completion failed.")
                        self.current_candidates = [text]
                elif text.startswith("read ") or text.startswith("fork ") or \
                     text.startswith("edit ") or text.startswith("copy "):
                    # Already started typing a snippet name
                    cmd, partial = text.split(" ", 1)
                    cmd = cmd + " "
                    try:
                        snippets = self.repo.get_snippet_names() if hasattr(self.repo, 'get_snippet_names') else []
                        self.current_candidates = [cmd + snippet for snippet in snippets if snippet.startswith(partial)]
                    except:
                        print("completion failed.")
                        self.current_candidates = []
                elif text == "help ":
                    # Complete with command names for help
                    self.current_candidates = [text + cmd for cmd in self.command_names]
                elif text.startswith("help "):
                    # Complete partial command name for help
                    cmd, partial = text.split(" ", 1)
                    cmd = cmd + " "
                    self.current_candidates = [cmd + command for command in self.command_names if command.startswith(partial)]
                else:
                    # Complete command names
                    self.current_candidates = [cmd for cmd in self.commands if cmd.startswith(text)]

            # Return the state-th candidate, or None if no more candidates
            return self.current_candidates[state] if state < len(self.current_candidates) else None

    # Set up history file
    history_file = os.path.expanduser("~/.pd_history")
    try:
        readline.read_history_file(history_file)
        # Set history length
        readline.set_history_length(1000)
    except FileNotFoundError:
        # History file doesn't exist yet
        pass

    # Register history save on exit
    import atexit
    atexit.register(lambda: readline.write_history_file(history_file))

    # Set up tab completion
    completer = CommandCompleter(repo)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")


def get_general_help():
    """Return general help text"""
    return """
    Available commands:

    help                  Display this help information
    help <command>        Display detailed help for a specific command
    exit                  Exit the application

    list                  List all available snippets
    read <user/snippet>   Read a snippet from a user's branch
    write <user/snippet> --content <content>  Write content to a snippet
    fork <user/snippet>   Copy a snippet from another user to your branch
    edit <user/snippet>   Open a snippet in your default editor
    copy <user/snippet>   Copy a snippet to your clipboard
    sync                  Synchronize all branches with remote repository
    new <filename>        Create a new prompt file

    For more detailed help on any command, type 'help <command>'.
    """


def get_command_help(command):
    """Return help text for a specific command"""
    help_texts = {
        "help": """
        Usage: help [command]
        Description: Display help information.
        If a command is specified, show detailed help for that command.
        """,

        "list": """
        Usage: list
        Description: List all available snippets in the repository.
        """,

        "read": """
        Usage: read <user/snippet>
        Description: Read a snippet from a user's branch.
        The address format is 'user/snippet'.

        Example: read johndoe/greeting
        """,

        "write": """
        Usage: write <user/snippet> --content "your content here"
        Description: Write content to a snippet in your branch.
        The address format is 'yourusername/snippet'.

        Example: write myuser/greeting --content "Hello, world!"
        """,

        "fork": """
        Usage: fork <user/snippet>
        Description: Copy a snippet from another user's branch to your branch.
        The address format is 'user/snippet'.

        Example: fork johndoe/greeting
        """,

        "edit": """
        Usage: edit <user/snippet>
        Description: Open a snippet in your default editor.
        The address format is 'user/snippet'.

        Example: edit myuser/greeting
        """,

        "copy": """
        Usage: copy <user/snippet> [--hydrate --arg1="value1" --arg2="value2" -- suffix]
        Description: Copy a snippet to your clipboard.
        The address format is 'user/snippet'.
        Add --hydrate to process template variables.

        Example: copy johndoe/greeting
        Example with hydration: copy johndoe/template --hydrate --name="John" -- Additional text
        """,

        "sync": """
        Usage: sync
        Description: Synchronize all branches with the remote repository.
        """,

        "new": """
        Usage: new <filename>
        Description: Create a new prompt file in your branch.

        Example: new greeting
        """,

        "exit": """
        Usage: exit
        Description: Exit the application.
        """
    }

    if command in help_texts:
        return textwrap.dedent(help_texts[command])
    else:
        return f"No help available for '{command}'. Type 'help' for a list of commands."


def parse_inline_command(command):
    """Parse an inline command into template name, args, and suffix"""
    # First split on -- to separate main command and suffix
    parts = command.strip().split(' -- ')
    main_part = parts[0]
    suffix = parts[1] if len(parts) > 1 else ''

    # Extract template name and args from main part
    template_pattern = r'^(\w+/?\w*)'
    template_match = re.match(template_pattern, main_part)
    if not template_match:
        raise ValueError(f"Invalid command format: {command}")

    template_name = template_match.group(1)

    # Extract arguments
    arg_pattern = r'--([\w-]+)="([^"]*?)"'
    args = {}
    for match in re.finditer(arg_pattern, main_part):
        args[match.group(1)] = match.group(2)

    return template_name, args, suffix


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


def load_config() -> dict:
    """Load configuration from config file"""
    if not CONFIG_FILE.exists():
        # Create default config
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "prompt_repo": ""
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config: dict):
    """Save configuration to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def interactive_mode(repo):
    """Run the interactive REPL mode"""
    # Set up readline if available
    setup_readline(repo)

    print("Prompt Directory REPL. Type 'help' for available commands.")
    while True:
        try:
            cmd = input("> ").strip()
            if cmd == "exit" or cmd == "q":
                break
            elif cmd == "help" or cmd == "h" or cmd == "?":
                print(get_general_help())
                continue
            elif cmd.startswith("help ") or cmd.startswith("h "):
                command = cmd.split(maxsplit=1)[1]
                print(get_command_help(command))
                continue
            elif cmd == "list" or cmd == "ls" or cmd == "l":
                repo.list_snippet_names()
                continue
            elif cmd.startswith("read ") or cmd.startswith("r "):
                address = cmd.split(maxsplit=1)[1]
                if not address:
                    print("Usage: read <user/snippet>")
                    continue
                repo.read_snippet(address)
                continue
            elif cmd.startswith("fork "):
                address = cmd.split(maxsplit=1)[1]
                if not address:
                    print("Usage: fork <user/snippet>")
                    continue
                repo.fork_snippet(address)
                continue
            elif cmd.startswith("write "):
                if not " --content " in cmd:
                    raise ValueError("Missing --content argument for write command")
                cmd = cmd.replace("write ", "")
                address, content = cmd.split(" --content ")
                repo.write_snippet(address, content)
                continue
            elif cmd.startswith("edit "):
                address = cmd.split(maxsplit=1)[1]
                if not address:
                    print("Usage: edit <user/snippet>")
                    continue
                repo.edit_snippet(address)
                continue
            elif cmd.startswith("copy "):
                parts = cmd.split(maxsplit=1)[1].split()
                if not parts:
                    print("Usage: copy <user/snippet> [--hydrate --arg1=\"value1\" --arg2=\"value2\" -- suffix]")
                    continue

                address = parts[0]

                # Check if we should hydrate
                if len(parts) > 1 and "--hydrate" in parts:
                    # Extract arguments for hydration
                    hydrate_args = {}

                    # Parse named arguments
                    arg_matches = re.finditer(r'--(\w+)="([^"]*?)"', cmd)
                    for m in arg_matches:
                        arg_name = m.group(1)
                        if arg_name != "hydrate":  # Skip the --hydrate flag
                            hydrate_args[arg_name] = m.group(2)

                    # Get suffix after --
                    suffix_match = re.search(r'\s+--\s+(.*?)$', cmd)
                    if suffix_match:
                        hydrate_args['suffix'] = suffix_match.group(1)

                    repo.copy_snippet(address, hydrate_args)
                else:
                    # Just copy the raw snippet
                    repo.copy_snippet(address)
                continue
            elif cmd == "sync":
                repo.sync_all()
                continue
            elif cmd.startswith("new "):
                _, filename = cmd.split(maxsplit=1)
                repo.create_new_prompt_file(repo.get_worktree(repo.get_username()), filename)
                continue

            # Default case, handle the command
            name, args, suffix = parse_inline_command(cmd)
            if "/" not in name:
                name = f"{repo.get_username()}/{name}"
            output = repo.hydrate(name, args, suffix)
            print("\"\"\"")
            print(output)
            print("\"\"\"")
            print()

            print("Opening in browser 🌐")
            open_in_browser(output)

        except Exception as e:
            print(e)
            print(f"Error: {traceback.format_exc()}")


def main():
    """Main entry point for the pd command"""
    # Define merged argument parser
    parser = argparse.ArgumentParser(description="Prompt Directory - Manage GitHub-based prompts")

    # Configuration options
    parser.add_argument('--repo', help='Specify prompt repository (e.g. username/repo)')
    parser.add_argument('--no-ssh', action='store_true', help='Skip SSH agent setup')
    parser.add_argument('--base-dir', default="~/.git_worktree_cache", help='Local cache directory')

    # Command options (similar to subcommands)
    parser.add_argument('command', nargs='?', help='Command to execute (read, write, list, etc.)')
    parser.add_argument('address', nargs='?', help='Snippet address in user/snippet format')
    parser.add_argument('--content', help='Content for write command')

    args, remaining_args = parser.parse_known_args()

    # Load configuration
    config = load_config()

    # Override config with command line arguments
    prompt_repo = args.repo or config.get('prompt_repo')
    base_dir = os.path.expanduser(args.base_dir)
    save_config({"prompt_repo": prompt_repo})

    if not prompt_repo:
        print("Error: No prompt repository specified. Use --repo to set it. The last used repo will be remembered.")
        return 1

    # Setup SSH agent if not disabled
    if not args.no_ssh:
        setup_ssh_agent()

    # Initialize the repository
    repo = SnippetRepo(prompt_repo, base_dir=base_dir)
    repo.ensure_self_branch()

    # If no command is provided, run in interactive mode
    if not args.command:
        interactive_mode(repo)
        return 0

    # Otherwise, handle specific commands
    try:
        if args.command == "list":
            repo.list_snippet_names()
        elif args.command == "read" and args.address:
            repo.read_snippet(args.address)
        elif args.command == "write" and args.address and args.content:
            repo.write_snippet(args.address, args.content)
        elif args.command == "fork" and args.address:
            repo.fork_snippet(args.address)
        elif args.command == "edit" and args.address:
            repo.edit_snippet(args.address)
        elif args.command == "sync":
            repo.sync_all()
        elif args.command == "new" and args.address:  # Using address parameter for filename
            repo.create_new_prompt_file(repo.get_worktree(repo.get_username()), args.address)
        elif args.command == "copy" and args.address:
            # Handle copying with optional hydration
            hydrate_args = None
            if "--hydrate" in remaining_args:
                hydrate_args = {}
                # Parse any key-value args from remaining_args
                for i, arg in enumerate(remaining_args):
                    if arg.startswith("--") and arg != "--hydrate" and i + 1 < len(remaining_args):
                        key = arg[2:]
                        value = remaining_args[i + 1]
                        hydrate_args[key] = value

            repo.copy_snippet(args.address, hydrate_args)
        else:
            # Try to handle as template hydration
            name = args.command
            username = repo.get_username()
            if "/" not in name and username:
                name = f"{username}/{name}"

            # Parse any arguments in remaining_args
            template_args = {}
            for i, arg in enumerate(remaining_args):
                if arg.startswith("--") and i + 1 < len(remaining_args):
                    key = arg[2:]
                    value = remaining_args[i + 1]
                    template_args[key] = value

            # Try to get suffix if -- is present
            suffix = ""
            try:
                dash_idx = remaining_args.index("--")
                if dash_idx < len(remaining_args) - 1:
                    suffix = " ".join(remaining_args[dash_idx + 1:])
            except ValueError:
                pass

            output = repo.hydrate(name, template_args, suffix)
            print(output)

            open_in_browser(output)

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def open_in_browser(content):
    url = f"https://github.com/copilot?prompt={content}"
    import webbrowser
    webbrowser.open(url)


if __name__ == "__main__":
    main()

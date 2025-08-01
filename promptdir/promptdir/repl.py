"""Interactive REPL for the Prompt Directory CLI."""

import os
import re
import traceback

from promptdir.commands import (
    list_snippets, read_snippet, write_snippet, fork_snippet,
    edit_snippet, copy_snippet, sync_all, create_new_prompt,
    get_help, get_command_help
)
from promptdir.commands.copy_cmd import parse_copy_args
from promptdir.utils.browser import open_in_browser

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


def setup_readline(repo, history: bool):
    """Set up readline for command history and tab completion"""
    if not READLINE_AVAILABLE:
        return

    # Define command completer class
    class CommandCompleter:
        """Tab completion for the REPL."""

        def __init__(self, repo):
            self.repo = repo

            # Define command names without spaces
            self.command_names = ["list", "read", "fork", "write", "edit", "copy", "new", "sync", "exit", "help"]
            self.command_aliases = {
                "list": ["ls", "l"],
                "read": ["r"],
                "fork": [],
                "write": ["w"],
                "edit": ["e"],
                "copy": ["c"],
                "new": ["n"],
                "sync": ["s"],
                "exit": ["q"],
                "help": ["h", "?"]
            }

            # Create all command names (no spaces)
            self.all_command_names = self.command_names.copy()
            for cmd, aliases in self.command_aliases.items():
                self.all_command_names.extend(aliases)

            # Commands that need snippet completion
            self.snippet_commands = ["read", "r", "fork", "edit", "e", "copy", "c"]

            # Current completion candidates
            self.current_candidates = []

        def get_snippet_names(self):
            """Safely get snippet names from repo"""
            try:
                if hasattr(self.repo, 'get_snippet_names'):
                    return self.repo.get_snippet_names()
                elif hasattr(self.repo, 'list_snippet_names'):
                    # Try to access snippets in another way
                    # For this example, we'll return an empty list
                    return []
                return []
            except Exception:
                return []

        def complete(self, text, state):
            """Return the state-th completion for text."""
            # Only generate candidates on first call (state == 0)
            if state == 0:
                line = readline.get_line_buffer()
                words = line.split()

                # Case 1: Empty input or just starting to type
                if not line.strip():
                    self.current_candidates = self.all_command_names

                # Case 2: First word completion (command name)
                elif len(words) == 1 and not line.endswith(' '):
                    # Complete partial command name
                    self.current_candidates = [cmd for cmd in self.all_command_names if cmd.startswith(text)]

                # Case 3: Command is complete, working on arguments
                elif line.endswith(' ') or len(words) > 1:
                    command = words[0].lower()

                    # Help command - suggest other commands as completions
                    if command in ['help', 'h', '?']:
                        if len(words) == 1:  # Just typed 'help '
                            self.current_candidates = self.command_names
                        else:  # Typed 'help' and partial command
                            partial = words[1] if len(words) > 1 else ''
                            self.current_candidates = [cmd for cmd in self.command_names if cmd.startswith(partial)]

                    # Commands that use snippet names
                    elif command in self.snippet_commands:
                        snippet_names = self.get_snippet_names()
                        if len(words) == 1:  # Just typed 'command '
                            self.current_candidates = snippet_names
                        else:  # Typed 'command' and partial snippet name
                            partial = words[1] if len(words) > 1 else ''
                            self.current_candidates = [s for s in snippet_names if s.startswith(partial)]

                    # Write command
                    elif command in ['write', 'w']:
                        if len(words) == 1:  # Just typed 'write '
                            self.current_candidates = self.get_snippet_names()
                        elif len(words) == 2 and not line.endswith(' '):  # Completing snippet name
                            partial = words[1]
                            self.current_candidates = [s for s in self.get_snippet_names() if s.startswith(partial)]
                        elif len(words) == 2 and line.endswith(' '):  # Need content flag
                            self.current_candidates = ['--content']
                        elif len(words) > 2 and '--content' not in line:  # Suggest content flag
                            self.current_candidates = ['--content']

                    # New command
                    elif command in ['new', 'n'] and len(words) == 1:
                        # Suggest common file names
                        self.current_candidates = ['greeting', 'template', 'code', 'prompt', 'script']

                    # No completions for other commands
                    else:
                        self.current_candidates = []

                # No matches for other cases
                else:
                    self.current_candidates = []

            # Return the state-th candidate or None
            if state < len(self.current_candidates):
                return self.current_candidates[state]
            else:
                return None

    if history:
        # Set up history file
        history_file = os.path.expanduser("~/pd_history")
        try:
            readline.read_history_file(history_file)
            # Set history length
            readline.set_history_length(1000)
        except FileNotFoundError:
            # History file doesn't exist yet
            pass
        except PermissionError:
            pass

        # Register history save on exit
        import atexit
        atexit.register(lambda: readline.write_history_file(history_file))

    # Set up tab completion
    completer = CommandCompleter(repo)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")


def parse_inline_command(command):
    # First split on -- to separate main command and suffix
    parts = command.strip().split(' -- ')
    main_part = parts[0]
    suffix = parts[1] if len(parts) > 1 else ''

    # Extract template name and args from main part
    template_pattern = r'^(\w+/?\w*)'
    template_match = re.match(template_pattern, main_part)
    if not template_match:
        raise ValueError("Invalid command format. Use: command [--arg=\"val\"] [-- suffix]")
    template_name = template_match.group(1)

    # Parse named arguments
    args = {}
    arg_matches = re.finditer(r'--(\w+)="([^"]*?)"', main_part)
    for m in arg_matches:
        args[m.group(1)] = m.group(2)

    return template_name, args, suffix


def interactive_mode(repo, history: bool, browser: bool, ollama: bool):
    """Run the interactive REPL mode"""
    # Set up readline if available
    setup_readline(repo, history)

    print("Prompt Directory REPL. Type 'help' for available commands.")
    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            
            # Exit commands
            if cmd == "exit" or cmd == "q":
                break

            # Help commands
            elif cmd == "help" or cmd == "h" or cmd == "?":
                print(get_help())
                continue
            elif cmd.startswith("help ") or cmd.startswith("h "):
                command = cmd.split(maxsplit=1)[1]
                print(get_command_help(command))
                continue

            # List command
            elif cmd == "list" or cmd == "ls" or cmd == "l":
                list_snippets(repo)
                continue

            # Read command
            elif cmd.startswith("read ") or cmd.startswith("r "):
                address = cmd.split(maxsplit=1)[1]
                read_snippet(repo, address)
                continue

            # Fork command
            elif cmd.startswith("fork "):
                address = cmd.split(maxsplit=1)[1]
                fork_snippet(repo, address)
                continue

            # Write command
            elif cmd.startswith("write ") or cmd.startswith("w "):
                if " --content " not in cmd:
                    raise ValueError("Missing --content argument for write command")
                cmd = cmd.replace("write ", "").replace("w ", "")
                address, content = cmd.split(" --content ")
                write_snippet(repo, address, content)
                continue

            # Edit command
            elif cmd.startswith("edit ") or cmd.startswith("e "):
                address = cmd.split(maxsplit=1)[1]
                edit_snippet(repo, address)
                continue

            # Copy command
            elif cmd.startswith("copy ") or cmd.startswith("c "):
                if cmd.startswith("c "):
                    cmd = "copy " + cmd[2:]
                address, hydrate_args, should_hydrate = parse_copy_args(cmd)
                copy_snippet(repo, address, hydrate_args, should_hydrate)
                continue

            # Sync command
            elif cmd == "sync" or cmd == "s":
                sync_all(repo)
                continue

            # New command
            elif cmd.startswith("new ") or cmd.startswith("n "):
                _, filename = cmd.split(maxsplit=1)
                current_username = repo.get_username()
                create_new_prompt(repo, filename)
                continue

            # Default case, handle as template hydration
            name, args, suffix = parse_inline_command(cmd)
            if "/" not in name:
                current_username = repo.get_username()
                name = f"{current_username}/{name}"
            output = repo.hydrate(name, args, suffix)
            print("\"\"\"")
            print(output)
            print("\"\"\"")
            print()

            if browser:
                print("Opening in browser 🌐")
                open_in_browser(output)
            
            if ollama:
                from promptdir.utils.ollama_runner import run_ollama_prompt
                run_ollama_prompt(output)

        except KeyboardInterrupt:
            print()
            print("Exiting...")
            exit(0)
        except Exception as e:
            print(e)
            print(f"Error: {traceback.format_exc()}")

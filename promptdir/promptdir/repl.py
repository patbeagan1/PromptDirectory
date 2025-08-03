"""Interactive REPL for the Prompt Directory CLI."""

import os
import re
import traceback

from promptdir.commands import (
    list_items, read_item, write_item, fork_item,
    edit_item, copy_item, sync_all, create_new_item,
    get_help, get_command_help, delete_item, search_items, rename_item
)
from promptdir.commands.copy_cmd import parse_copy_args
from promptdir.utils.browser import open_in_browser
from promptdir.utils.snippet_repo import PromptRepo, SnippetRepo, ScriptRepo

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
            self.command_names = ["list", "read", "fork", "write", "edit", "copy", "new", "sync", "exit", "help",
                                  "delete", "search", "rename", "use", "run"]
            self.command_aliases = {
                "list": ["ls", "l"], "read": ["r"], "fork": [], "write": ["w"], "edit": ["e"],
                "copy": ["c"], "new": ["n"], "sync": ["s"], "exit": ["q"], "help": ["h", "?"],
                "delete": ["del", "rm"], "search": ["grep", "find"], "rename": ["mv", "move"],
                "use": [], "run": [],
            }

            # Create all command names (no spaces)
            self.all_command_names = self.command_names.copy()
            for cmd, aliases in self.command_aliases.items():
                self.all_command_names.extend(aliases)

            # Commands that need item completion
            self.item_commands = ["read", "r", "fork", "edit", "e", "copy", "c", "delete", "del", "rm", "rename", "mv",
                                  "move", "run"]

            # Current completion candidates
            self.current_candidates = []

        def get_item_names(self):
            """Safely get item names from repo"""
            try:
                return self.repo.get_item_names()
            except Exception:
                return []

        def complete(self, text, state):
            """Return the state-th completion for text."""
            if state == 0:
                line = readline.get_line_buffer()
                words = line.split()

                if not line.strip():
                    self.current_candidates = self.all_command_names
                elif len(words) == 1 and not line.endswith(' '):
                    self.current_candidates = [cmd for cmd in self.all_command_names if cmd.startswith(text)]
                elif line.endswith(' ') or len(words) > 1:
                    command = words[0].lower()

                    if command in ['help', 'h', '?']:
                        self.current_candidates = self.command_names if len(
                            words) == 1 else [cmd for cmd in self.command_names if cmd.startswith(words[1])]
                    elif command == 'use':
                        self.current_candidates = ['prompt', 'snippet', 'script']
                    elif command in self.item_commands:
                        item_names = self.get_item_names()
                        partial = words[1] if len(words) > 1 else ''
                        self.current_candidates = [s for s in item_names if s.startswith(partial)]
                    else:
                        self.current_candidates = []
                else:
                    self.current_candidates = []

            return self.current_candidates[state] if state < len(self.current_candidates) else None

    if history:
        history_file = os.path.expanduser("~/pd_history")
        try:
            readline.read_history_file(history_file)
            readline.set_history_length(1000)
        except (FileNotFoundError, PermissionError):
            pass
        import atexit
        atexit.register(lambda: readline.write_history_file(history_file))

    completer = CommandCompleter(repo)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")


def parse_inline_command(command):
    parts = command.strip().split(' -- ')
    main_part = parts[0]
    suffix = parts[1] if len(parts) > 1 else ''

    template_match = re.match(r'^(\w+/?\w*)', main_part)
    if not template_match:
        raise ValueError("Invalid command format.")
    template_name = template_match.group(1)

    args = {m.group(1): m.group(2) for m in re.finditer(r'--(\w+)="([^"]*?)"', main_part)}
    return template_name, args, suffix


def interactive_mode(repo, history: bool, browser: bool, ollama: bool):
    """Run the interactive REPL mode"""
    setup_readline(repo, history)
    repo_type = 'prompt'
    print("Prompt Directory REPL. Type 'help' for available commands.")

    while True:
        try:
            prompt = f"({repo_type}) > "
            cmd = input(prompt).strip()
            if not cmd:
                continue

            parts = cmd.split()
            command = parts[0]
            args = parts[1:]

            if command in ["exit", "q"]:
                break
            elif command in ["help", "h", "?"]:
                print(get_command_help(args[0]) if args else get_help(repo_type))
            elif command == "use" and args:
                new_type = args[0]
                if new_type in ['prompt', 'snippet', 'script']:
                    if new_type != repo_type:
                        repo_type = new_type
                        if new_type == 'prompt':
                            repo = PromptRepo(repo.repo_slug, base_dir=repo.base_dir)
                        elif new_type == 'snippet':
                            repo = SnippetRepo(repo.repo_slug, base_dir=repo.base_dir)
                        elif new_type == 'script':
                            repo = ScriptRepo(repo.repo_slug, base_dir=repo.base_dir)
                        setup_readline(repo, history) # Re-initialize completer with new repo
                    print(f"Switched to {repo_type} mode.")
                else:
                    print("Invalid type. Choose 'prompt', 'snippet', or 'script'.")
            elif command in ["list", "ls", "l"]:
                list_items(repo)
            elif command in ["read", "r"] and args:
                read_item(repo, args[0])
            elif command == "fork" and args:
                fork_item(repo, args[0])
            elif command in ["write", "w"] and args:
                address = args[0]
                content_marker = "--content"
                if content_marker in args:
                    content_index = args.index(content_marker)
                    content = " ".join(args[content_index + 1:])
                    write_item(repo, address, content)
                else:
                    print("Usage: write <address> --content <content>")
            elif command in ["edit", "e"] and args:
                edit_item(repo, args[0])
            elif command in ["copy", "c"] and args:
                address, hydrate_args, should_hydrate = parse_copy_args(cmd)
                copy_item(repo, address, hydrate_args, should_hydrate)
            elif command in ["sync", "s"]:
                sync_all(repo)
            elif command in ["new", "n"] and args:
                create_new_item(repo, args[0])
            elif command in ["delete", "del", "rm"] and args:
                delete_item(repo, args[0])
            elif command in ["search", "grep", "find"] and args:
                search_items(repo, " ".join(args))
            elif command in ["rename", "mv", "move"] and len(args) == 2:
                rename_item(repo, args[0], args[1])
            elif command == "run" and args and isinstance(repo, ScriptRepo):
                repo.run(args[0], args[1:])
            elif isinstance(repo, PromptRepo):
                name, template_args, suffix = parse_inline_command(cmd)
                if "/" not in name:
                    name = f"{repo.get_username()}/{name}"
                output = repo.hydrate(name, template_args, suffix)
                print(f'"""\n{output}\n"""\n')
                if browser:
                    print("Opening in browser 🌐")
                    open_in_browser(output)
                if ollama:
                    from promptdir.utils.ollama_runner import run_ollama_prompt
                    run_ollama_prompt(output)
            else:
                print(f"Command not found or not applicable for type '{repo_type}'.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception:
            print(f"Error: {traceback.format_exc()}")
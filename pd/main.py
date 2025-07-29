import argparse
import re
import sys
import traceback
import webbrowser
import os
import textwrap

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

from snippet_repo import SnippetRepo


# --- Main REPL ---
def main():
    """
    Command-line interface for managing GitHub-based snippets using git worktrees.

    This function provides a CLI with the following subcommands:
    - help: Display help information (help [command])
    - read: Read a snippet from a user's branch (address format: user/snippet)
    - write: Write a snippet to your branch (address format: yourusername/snippet)
    - fork: Copy a snippet from another user's branch to your branch (address format: user/snippet)
    - list: Show all available snippets
    - sync: Synchronize all branches with remote repository

    Command line arguments:
        repo: GitHub repository slug (e.g. org/repo)
        --base-dir: Local cache directory (default: ~/.git_worktree_cache)

    Example usage:
        python script.py org/repo read user/snippet
        python script.py org/repo write myuser/snippet --content "snippet text"
        python script.py org/repo list
        python script.py org/repo sync
    """

    parser = argparse.ArgumentParser(description="GitHub snippet snippet_manager (gh + git worktree)")
    parser.add_argument("repo", help="GitHub repo slug (e.g. org/repo)")
    parser.add_argument("user", help="The current user's username")
    parser.add_argument("--base-dir", default="~/.git_worktree_cache", help="Local cache directory")
    args = parser.parse_args()

    repo = SnippetRepo(args.repo, base_dir=args.base_dir)

    if len(sys.argv) > 3:
        print("TODO")
        exit(1)
        # Handle inline hydration from CLI
        # cmd = " ".join(sys.argv[1:]).strip()
        # try:
        #     if cmd.startswith("/new "):
        #         _, filename = cmd.split(maxsplit=1)
        #         create_new_prompt_file(repo.get_worktree(args.user), filename)
        #     elif cmd == "/list ":
        #         print("\n".join(TEMPLATES.keys()))
        #     else:
        #         name, args, suffix = parse_inline_command(cmd)
        #         output = hydrate(name, args, suffix)
        #         print(output)
        # except Exception as e:
        #     print(f"Error: {e}")
    else:
        username = repo.get_username()
        repo.ensure_self_branch()

        # Set up readline if available
        setup_readline(repo)

        # Start interactive REPL
        print(
            "Hydrator REPL. Type 'help' for available commands.")
        while True:
            try:
                cmd = input("> ").strip()
                if cmd == "exit":
                    break
                elif cmd == "help":
                    print(get_general_help())
                    continue
                elif cmd.startswith("help "):
                    command = cmd.split(maxsplit=1)[1]
                    print(get_command_help(command))
                    continue
                elif cmd == "list":
                    repo.list_snippet_names()
                    continue
                elif cmd.startswith("read "):
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
                elif cmd.startswith("write ") and " --content " in cmd:
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
                        arg_matches = re.finditer(r'--([\w-]+)="([^"]*?)"', cmd)
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
                    repo.create_new_prompt_file(repo.get_worktree(username), filename)
                    continue

                # Default case, handle the command
                name, args, suffix = parse_inline_command(cmd)
                if "/" not in name:
                    name = f"{username}/{name}"
                output = repo.hydrate(name, args, suffix)
                print("\"\"\"")
                print(output)
                print("\"\"\"")
                print()
                print("Opening in browser 🌐")
                open_in_browser(output)

            except Exception as e:
                # print(f"Error: {e}")
                print(f"Error: {traceback.format_exc()}")


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
                self.current_candidates = [text + snippet for snippet in self.repo.get_snippet_names()]
            elif text.startswith("read ") or text.startswith("fork ") or \
                 text.startswith("edit ") or text.startswith("copy "):
                # Already started typing a snippet name
                cmd, partial = text.split(" ", 1)
                cmd = cmd + " "
                snippets = self.repo.get_snippet_names()
                self.current_candidates = [cmd + snippet for snippet in snippets if snippet.startswith(partial)]
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


def setup_readline(repo):
    """Set up readline with history and tab completion."""
    if not READLINE_AVAILABLE:
        return

    # Set up history file
    history_file = os.path.expanduser("~/.snippet_repo_history")
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


def open_in_browser(content):
    url = f"https://github.com/copilot?prompt={content}"
    webbrowser.open(url)


def get_general_help():
    """Return general help information for the application."""
    help_text = """
    GitHub Snippet Manager Help
    =========================

    This is a tool for managing GitHub-based snippets using git worktrees.

    Available Commands:
      help                 Show this help message
      help <command>       Show help for a specific command
      list                 Show all available snippets
      read <user/snippet>  Read a snippet from a user's branch
      write <user/snippet> --content <text>  Write a snippet to your branch
      fork <user/snippet>  Copy a snippet from another user to your branch
      edit <user/snippet>  Open a snippet in your default text editor
      copy <user/snippet>  Copy a snippet to clipboard
      new <filename>       Create a new prompt file
      sync                 Synchronize all branches with remote repository
      exit                 Exit the application

    For more information on a specific command, type 'help <command>'.
    """
    return textwrap.dedent(help_text)

def get_command_help(command):
    """Return help information for a specific command."""
    help_texts = {
        "list": """
        Command: list
        Usage: list
        Description: Lists all available snippets across all branches.

        This command shows a list of all available snippets in the repository,
        organized by username (branch). Use this to discover what snippets are
        available for reading or forking.
        """,

        "read": """
        Command: read
        Usage: read <user/snippet>
        Description: Read a snippet from a user's branch.

        Arguments:
          <user/snippet>  The address of the snippet in the format 'username/snippetname'

        Example:
          read johndoe/my-cool-snippet
        """,

        "write": """
        Command: write
        Usage: write <user/snippet> --content <text>
        Description: Write a snippet to your branch.

        Arguments:
          <user/snippet>  The address of the snippet in the format 'yourusername/snippetname'
          --content      The text content to write to the snippet

        Example:
          write myusername/new-snippet --content "This is my new snippet content."
        """,

        "fork": """
        Command: fork
        Usage: fork <user/snippet>
        Description: Copy a snippet from another user's branch to your branch.

        Arguments:
          <user/snippet>  The address of the snippet to fork in the format 'username/snippetname'

        Example:
          fork johndoe/cool-snippet
        """,

        "edit": """
        Command: edit
        Usage: edit <user/snippet>
        Description: Open a snippet in your default text editor.

        Arguments:
          <user/snippet>  The address of the snippet to edit in the format 'username/snippetname'

        Example:
          edit myusername/my-snippet
        """,

        "copy": """
        Command: copy
        Usage: copy <user/snippet> [--hydrate --arg1="value1" --arg2="value2" -- suffix]
        Description: Copy a snippet to clipboard, with optional hydration (template expansion).

        Arguments:
          <user/snippet>  The address of the snippet to copy in the format 'username/snippetname'
          --hydrate       Flag to enable template hydration
          --arg=value     Named arguments for template hydration
          -- suffix       Optional suffix text to append after hydration

        Example:
          copy johndoe/template-snippet
          copy johndoe/template-snippet --hydrate --name="John" --age="42" -- Additional text
        """,

        "new": """
        Command: new
        Usage: new <filename>
        Description: Create a new prompt file in your branch.

        Arguments:
          <filename>  The name of the new file to create

        Example:
          new my-new-prompt
        """,

        "sync": """
        Command: sync
        Usage: sync
        Description: Synchronize all branches with the remote repository.

        This command pulls the latest changes from the remote repository for all
        local branches, ensuring you have the most up-to-date content.
        """,

        "help": """
        Command: help
        Usage: help [command]
        Description: Display help information.

        Arguments:
          [command]  Optional command name to get specific help for

        Examples:
          help          Show general help
          help read     Show help for the 'read' command
        """,

        "exit": """
        Command: exit
        Usage: exit
        Description: Exit the application.
        """
    }

    if command in help_texts:
        return textwrap.dedent(help_texts[command])
    else:
        return f"No help available for '{command}'. Type 'help' for a list of commands."

def parse_inline_command(command):
    pattern = r"^(\w+/?\w*)(?:\s+--(\w+)=\"([^\"]*)\")*(?:\s+--\s+(.*))?$"
    match = re.match(pattern, command.strip(), re.DOTALL)
    if not match:
        raise ValueError("Invalid command format. Use: command [--arg=\"val\"] [-- suffix]")
    template_name = match.group(1)

    # Parse args from repeated named groups
    args = {}
    matches = re.finditer(r'--(\w+)=\"([^\"]*?)\"', command)
    for m in matches:
        args[m.group(1)] = m.group(2)

    # Get suffix after --
    suffix_match = re.search(r'\s+--\s+(.*?)$', command)
    suffix = suffix_match.group(1) if suffix_match else ''

    return template_name, args, suffix


if __name__ == "__main__":
    """
    // it is scriptable
    for i in $(ls -1); do python3 main.py "/story {subject='$i' location='`pwd`'}"; done
    """
    main()

# import os
# import subprocess
# import argparse
# from pathlib import Path
#
# def sanitize_repo_name(repo_url):
#     return os.path.basename(repo_url).replace('.git', '').replace('/', '_')
#
# def embed_auth_token(repo_url, token):
#     if token and repo_url.startswith("https://"):
#         return repo_url.replace("https://", f"https://{token}@")
#     return repo_url
#
# def ensure_bare_repo(repo_url, bare_repo_path):
#     if not os.path.isdir(os.path.join(bare_repo_path, 'HEAD')):
#         subprocess.run(["git", "clone", "--bare", repo_url, bare_repo_path], check=True)
#
# def ensure_worktree(bare_repo_path, branch, branch_dir):
#     if not os.path.isdir(branch_dir):
#         subprocess.run([
#             "git", "--git-dir", bare_repo_path, "worktree", "add", "--track", "-b", branch, branch_dir, f"origin/{branch}"
#         ], check=True)
#     else:
#         subprocess.run(["git", "-C", branch_dir, "pull"], check=True)
#
# def read_snippet(address, repo_url, token, base_dir):
#     user, snippet = address.strip().split("/")
#     path = f"prompts/{snippet}.prompt.md"
#
#     repo_name = sanitize_repo_name(repo_url)
#     base_dir = os.path.expanduser(base_dir or "~/.git_worktree_cache")
#     bare_repo_path = os.path.join(base_dir, f"{repo_name}.bare")
#     branch_dir = os.path.join(base_dir, f"{repo_name}_{user}")
#
#     repo_url = embed_auth_token(repo_url, token)
#     ensure_bare_repo(repo_url, bare_repo_path)
#     ensure_worktree(bare_repo_path, user, branch_dir)
#
#     snippet_path = os.path.join(branch_dir, path)
#     if not os.path.isfile(snippet_path):
#         raise FileNotFoundError(f"No such snippet: {address} ({snippet_path})")
#
#     with open(snippet_path, 'r', encoding='utf-8') as f:
#         print(f.read())
#
# def write_snippet(address, repo_url, token, base_dir, content):
#     user, snippet = address.strip().split("/")
#     path = f"prompts/{snippet}.prompt.md"
#
#     repo_name = sanitize_repo_name(repo_url)
#     base_dir = os.path.expanduser(base_dir or "~/.git_worktree_cache")
#     bare_repo_path = os.path.join(base_dir, f"{repo_name}.bare")
#     branch_dir = os.path.join(base_dir, f"{repo_name}_{user}")
#
#     repo_url = embed_auth_token(repo_url, token)
#     ensure_bare_repo(repo_url, bare_repo_path)
#     ensure_worktree(bare_repo_path, user, branch_dir)
#
#     # Write the snippet
#     snippet_path = os.path.join(branch_dir, path)
#     os.makedirs(os.path.dirname(snippet_path), exist_ok=True)
#     with open(snippet_path, "w", encoding="utf-8") as f:
#         f.write(content)
#
#     # Commit the change
#     subprocess.run(["git", "-C", branch_dir, "add", snippet_path], check=True)
#     subprocess.run(["git", "-C", branch_dir, "commit", "-m", f"Update snippet {snippet}"], check=True)
#
#     # Push the branch
#     subprocess.run(["git", "-C", branch_dir, "push", "origin", user], check=True)
#     print(f"✅ Snippet '{snippet}' written to branch '{user}' and pushed.")
#
# # CLI glue
# def main():
#     parser = argparse.ArgumentParser(description="Collaborative Git-based text snippet tool")
#     parser.add_argument("repo", help="Git repository URL")
#     parser.add_argument("--token", help="GitHub token for private repo access", default=None)
#     parser.add_argument("--base-dir", help="Directory for storing repo and worktrees", default="~/.git_worktree_cache")
#     subparsers = parser.add_subparsers(dest="command", required=True)
#
#     # read user/snippet
#     parser_read = subparsers.add_parser("read", help="Read a snippet from someone’s branch")
#     parser_read.add_argument("address", help="user/snippet")
#
#     # write user/snippet --content
#     parser_write = subparsers.add_parser("write", help="Write a snippet to your own branch")
#     parser_write.add_argument("address", help="yourusername/snippet")
#     parser_write.add_argument("--content", help="Text content to write", required=True)
#
#     args = parser.parse_args()
#
#     if args.command == "read":
#         read_snippet(args.address, args.repo, args.token, args.base_dir)
#     elif args.command == "write":
#         write_snippet(args.address, args.repo, args.token, args.base_dir, args.content)
#
# if __name__ == "__main__":
#     main()

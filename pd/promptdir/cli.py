#!/usr/bin/env python3

import argparse
import os

from promptdir.utils.config import load_config, save_config
from promptdir.utils.ssh import setup_ssh_agent
from promptdir.utils.snippet_repo import SnippetRepo


def cli():
    """Main entry point for the promptdir command"""
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

    # Setup SSH agent if not already disabled
    if not args.no_ssh:
        setup_ssh_agent()

    # Initialize the repository
    repo = SnippetRepo(prompt_repo, base_dir=base_dir)
    repo.ensure_self_branch()

    # If no command is provided, run in interactive mode
    if not args.command:
        from promptdir.repl import interactive_mode
        interactive_mode(repo)
        return 0

    return handle_cli_command(args, remaining_args, repo)


def handle_cli_command(args, remaining_args, repo):
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

            from promptdir.utils.browser import open_in_browser
            open_in_browser(output)

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


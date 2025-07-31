"""Help command implementation."""

import textwrap

def get_help():
    """Return general help text"""
    return """
    Available commands:

    help                  Display this help information
    help <command>        Display detailed help for a specific command
    exit                  Exit the application

    new <filename>        Create a new prompt file
    list                  List all available snippets
    
    read <user/snippet>   Read a snippet from a user's branch
    write <snippet> --content <content>  
                          Write content to a snippet. 
                          It assumes the current user's branch.
    
    fork <user/snippet>   Copy a snippet from another user to your branch
    edit <snippet>        Open a snippet in your default editor
    copy <user/snippet>   Copy a snippet to your clipboard
    
    sync                  Synchronize all branches with remote repository
    
    For more detailed help on any command, type 'help <command>'.
    
    Or visit the readme: https://github.com/patbeagan1/PromptDirectory
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

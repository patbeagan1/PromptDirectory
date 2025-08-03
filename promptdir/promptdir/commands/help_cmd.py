"""Help command implementation."""

import textwrap

def get_help(mode='prompt'):
    """Return general help text based on the current mode."""
    mode_specific_help = ""
    if mode == 'script':
        mode_specific_help = "\n    run <user/script> [args] Run a script"
    elif mode == 'prompt':
        mode_specific_help = "\n    <user/prompt> [args]  Hydrate a prompt with arguments."

    return f"""
    Available commands:

    help                  Display this help information
    help <command>        Display detailed help for a specific command
    exit                  Exit the application
    use <type>            Switch content type (prompt, snippet, script)

    new <filename>        Create a new item file
    list                  List all available items
    
    read <user/item>      Read an item from a user's branch
    write <item> --content <content>  
                          Write content to an item. 
                          It assumes the current user's branch.
    
    fork <user/item>      Copy an item from another user to your branch
    edit <item>           Open an item in your default editor
    copy <user/item>      Copy an item to your clipboard
    
    sync                  Synchronize all branches with remote repository
    
    delete <user/item>    Delete an item from your branch
    search <query>        Search for a query in all items
    rename <source> <dest> Rename an item{mode_specific_help}

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
        
        "use": """
        Usage: use <type>
        Description: Switch the current content type.
        Type can be 'prompt', 'snippet', or 'script'.
        """,

        "list": """
        Usage: list
        Description: List all available items of the current type in the repository.
        """,

        "read": """
        Usage: read <user/item>
        Description: Read an item from a user's branch.
        The address format is 'user/item'.

        Example: read johndoe/greeting
        """,

        "write": """
        Usage: write <user/item> --content "your content here"
        Description: Write content to an item in your branch.
        The address format is 'yourusername/item'.

        Example: write greeting --content "Hello, world!"
        """,

        "fork": """
        Usage: fork <user/item>
        Description: Copy an item from another user's branch to your branch.
        The address format is 'user/item'.

        Example: fork johndoe/greeting
        """,

        "edit": """
        Usage: edit <user/item>
        Description: Open an item in your default editor.
        The address format is 'user/item'.

        Example: edit greeting
        """,

        "copy": """
        Usage: copy <user/item> [--hydrate --arg1="value1" --arg2="value2" -- suffix]
        Description: Copy an item to your clipboard.
        The address format is 'user/item'.
        For prompts, add --hydrate to process template variables.

        Example: copy johndoe/greeting
        Example with hydration: copy johndoe/template --hydrate --name="John" -- Additional text
        """,

        "sync": """
        Usage: sync
        Description: Synchronize all branches with the remote repository.
        """,

        "new": """
        Usage: new <filename>
        Description: Create a new item file in your branch.

        Example: new greeting
        """,

        "exit": """
        Usage: exit
        Description: Exit the application.
        """,

        "delete": """
        Usage: delete <user/item>
        Description: Deletes an item from your branch.
        The address format is 'yourusername/item'.

        Example: delete myusername/greeting
        """,

        "search": """
        Usage: search <query>
        Description: Searches for a query in all items of the current type.

        Example: search "hello world"
        """,
        
        "run": """
        Usage: run <user/script> [args...]
        Description: Executes a script from the repository.
        This command is only available for the 'script' type.
        
        Example: run myuser/my_script arg1 arg2
        """,
    }

    if command in help_texts:
        return textwrap.dedent(help_texts[command])
    else:
        return f"No help available for '{command}'. Type 'help' for a list of commands."
import re
from promptdir.utils.snippet_repo import PromptRepo

def copy_item(repo, address, args=None, hydrate=False):
    """Copy an item to the clipboard.

    Args:
        repo: The repository instance
        address: Item address in user/item format
        args: Optional arguments for hydration
        hydrate: Whether to process template variables
    """
    if not address:
        raise ValueError("Usage: copy <user/item> [--hydrate --arg1=\"value1\" --arg2=\"value2\" -- suffix]")

    if isinstance(repo, PromptRepo) and hydrate:
        hydrate_args = args or {}
        repo.copy_item(address, hydrate_args)
    else:
        repo.copy_item(address)

def parse_copy_args(cmd):
    """Parse copy command arguments.

    Args:
        cmd: The full command string

    Returns:
        Tuple of (address, hydrate_args, should_hydrate)
    """
    parts = cmd.split(maxsplit=1)[1].split()
    address = parts[0]
    hydrate_args = {}
    should_hydrate = False

    # Check if we should hydrate
    if len(parts) > 1 and "--hydrate" in parts:
        should_hydrate = True

        # Parse named arguments
        arg_matches = re.finditer(r'--([\w-]+)=\"([^\"]*?)\"', cmd)
        for m in arg_matches:
            arg_name = m.group(1)
            if arg_name != "hydrate":  # Skip the --hydrate flag
                hydrate_args[arg_name] = m.group(2)

        # Get suffix after --
        suffix_match = re.search(r'\s+--\s+(.*?)$', cmd)
        if suffix_match:
            hydrate_args['suffix'] = suffix_match.group(1)

    return address, hydrate_args, should_hydrate
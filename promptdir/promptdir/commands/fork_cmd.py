"""Fork command implementation."""

def fork_item(repo, address):
    """Fork an item from another user to your branch."""
    if not address:
        raise ValueError("Usage: fork <user/item>")
    repo.fork_item(address)
"""Edit command implementation."""

def edit_item(repo, address):
    """Open an item in the default editor."""
    if not address:
        raise ValueError("Usage: edit <user/item>")
    repo.edit_item(address)
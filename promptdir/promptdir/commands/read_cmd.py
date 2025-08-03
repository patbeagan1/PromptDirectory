"""Read command implementation."""

def read_item(repo, address):
    """Read an item from the repository."""
    if not address:
        raise ValueError("Usage: read <user/item>")
    repo.read_item(address)
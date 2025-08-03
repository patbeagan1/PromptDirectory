"""Delete command implementation."""

def delete_item(repo, address):
    """Delete an item from the repository."""
    if not address:
        raise ValueError("Usage: delete <user/item>")
    repo.delete_item(address)
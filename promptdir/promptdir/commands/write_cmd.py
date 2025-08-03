"""Write command implementation."""

def write_item(repo, address, content):
    """Write content to an item."""
    if not address or content is None:
        raise ValueError("Usage: write <user/item> --content \"your content\"")
    repo.write_item(address, content)
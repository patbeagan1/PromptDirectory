"""Write command implementation."""

def write_snippet(repo, address, content):
    """Write content to a snippet in the user's branch.

    Args:
        repo: The snippet repository
        address: Snippet address in user/snippet format
        content: Content to write to the snippet
    """
    if not address:
        raise ValueError("Usage: write <user/snippet> --content <content>")
    if not content:
        raise ValueError("Missing --content argument for write command")

    repo.write_snippet(address, content)

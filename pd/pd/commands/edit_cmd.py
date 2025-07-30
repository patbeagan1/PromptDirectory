"""Edit command implementation."""

def edit_snippet(repo, address):
    """Open a snippet in the default editor.

    Args:
        repo: The snippet repository
        address: Snippet address in user/snippet format
    """
    if not address:
        raise ValueError("Usage: edit <user/snippet>")
    repo.edit_snippet(address)

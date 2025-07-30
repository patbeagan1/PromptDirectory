"""Read command implementation."""

def read_snippet(repo, address):
    """Read a snippet from a user's branch.

    Args:
        repo: The snippet repository
        address: Snippet address in user/snippet format
    """
    if not address:
        raise ValueError("Usage: read <user/snippet>")
    repo.read_snippet(address)

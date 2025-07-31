"""Fork command implementation."""

def fork_snippet(repo, address):
    """Copy a snippet from another user's branch to your branch.

    Args:
        repo: The snippet repository
        address: Snippet address in user/snippet format
    """
    if not address:
        raise ValueError("Usage: fork <user/snippet>")
    repo.fork_snippet(address)

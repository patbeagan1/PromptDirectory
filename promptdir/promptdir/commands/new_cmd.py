"""New command implementation."""

def create_new_item(repo, filename):
    """Create a new item file in the user's branch.

    Args:
        repo: The repository instance
        filename: Name of the new item file
    """
    if not filename:
        raise ValueError("Usage: new <filename>")
    repo.create_new_file(repo.get_worktree(repo.get_username()), filename)
"""New command implementation."""

def create_new_prompt(repo, filename):
    """Create a new prompt file in the user's branch.

    Args:
        repo: The snippet repository
        filename: Name of the new prompt file
    """
    if not filename:
        raise ValueError("Usage: new <filename>")
    repo.create_new_prompt_file(repo.get_worktree(repo.get_username()), filename)

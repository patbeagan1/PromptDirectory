"""Rename command implementation."""

def rename_item(repo, source, dest):
    """Rename an item."""
    if not source or not dest:
        raise ValueError("Usage: rename <source> <destination>")
    repo.rename_item(source, dest)
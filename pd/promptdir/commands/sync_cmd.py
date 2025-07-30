"""Sync command implementation."""

def sync_all(repo):
    """Synchronize all branches with the remote repository."""
    repo.sync_all()
    repo.push()

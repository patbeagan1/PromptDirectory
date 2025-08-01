"""Rename command implementation."""

def rename_snippet(repo, source_address, destination_address):
    """Rename a snippet.

    Args:
        repo: The snippet repository
        source_address: The current address of the snippet
        destination_address: The new address for the snippet
    """
    if not source_address or not destination_address:
        raise ValueError("Usage: rename <source_address> <destination_address>")
    repo.rename_snippet(source_address, destination_address)

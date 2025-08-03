"""Search command implementation."""

def search_items(repo, query):
    """Search for a query in all items."""
    if not query:
        raise ValueError("Usage: search <query>")
    repo.search_items(query)
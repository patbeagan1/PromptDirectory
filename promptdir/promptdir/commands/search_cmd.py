"""Search command implementation."""

def search_snippets(repo, query):
    """Search for a query in all snippets.

    Args:
        repo: The snippet repository
        query: The text to search for
    """
    if not query:
        raise ValueError("Usage: search <query>")
    repo.search_snippets(query)

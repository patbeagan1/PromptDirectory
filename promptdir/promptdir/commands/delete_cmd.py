"""Delete command implementation."""
from promptdir.utils.snippet_repo import SnippetRepo


def delete_snippet(repo: SnippetRepo, address: str):
    """Delete a snippet from the user's branch.

    Args:
        repo: The snippet repository
        address: Snippet address in user/snippet format
    """
    if not address or "/" in address:
        raise ValueError("Invalid address. You can only delete snippets from your own branch.")

    # fix so that the address includes the username
    address = f"{repo.get_username()}/{address}"

    # It's a good practice to ask for confirmation before a destructive operation.
    print(f"Are you sure you want to delete '{address}'? [y/N]")
    confirmation = input("> ").lower()

    if confirmation == 'y':
        repo.delete_snippet(address)
    else:
        print("Deletion cancelled.")

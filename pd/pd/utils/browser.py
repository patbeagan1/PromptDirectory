"""Browser-related utilities."""

import webbrowser

def open_in_browser(content):
    """Open content in browser with GitHub Copilot URL."""
    url = f"https://github.com/copilot?prompt={content}"
    webbrowser.open(url)

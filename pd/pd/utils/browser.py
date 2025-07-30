"""Browser-related utilities."""


def open_in_browser(content):
    url = f"https://github.com/copilot?prompt={content}"
    import webbrowser
    webbrowser.open(url)

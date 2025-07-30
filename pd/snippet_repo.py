import os
import re
import subprocess
import sys
from pathlib import Path

from git_command_runner import GitCommandRunner

# Cross-platform clipboard functionality
try:
    import pyperclip


    def copy_to_clipboard(text):
        pyperclip.copy(text)
        return True
except ImportError:
    # Fallback clipboard implementations if pyperclip is not available
    def copy_to_clipboard(text):
        platform = sys.platform
        try:
            if platform == 'darwin':  # macOS
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return True
            elif platform == 'win32':  # Windows
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return True
            else:  # Linux and other platforms
                # Try xclip first
                try:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'))
                    return True
                except FileNotFoundError:
                    # Try xsel if xclip is not available
                    try:
                        process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
                        process.communicate(text.encode('utf-8'))
                        return True
                    except FileNotFoundError:
                        print("Warning: Could not find clipboard utilities. Please install pyperclip, xclip, or xsel.")
                        return False
        except Exception as e:
            print(f"Warning: Failed to copy to clipboard: {e}")
            return False


# https://gist.github.com/ChristopherA/4643b2f5e024578606b9cd5d2e6815cc


class TemplateManager:
    def __init__(self):
        self.cached_templates = {}

    def load_templates(self, snippets):
        """Reload template cache."""
        self.cached_templates = snippets

    def hydrate(self, template_name, args, suffix=""):
        """Fill template with provided arguments."""
        if template_name not in self.cached_templates:
            raise ValueError(f"Template '{template_name}' not found.")

        template = self.cached_templates[template_name]
        placeholders = re.findall(r"\{(.*?)}", template)

        missing = [key for key in placeholders if key not in args]
        if missing:
            raise ValueError(
                f"Missing required argument(s): {', '.join(missing)}.\n"
                f"Template requires: {', '.join(placeholders)}.\n"
                f"You provided: {', '.join(args.keys()) or 'none'}."
            )

        for key in placeholders:
            template = template.replace("{" + key + "}", args[key])

        extras = {k: v for k, v in args.items() if k not in placeholders}
        if extras:
            template += ", " + ", ".join(f"{k} is {v}" for k, v in extras.items())

        if suffix:
            template += ", " + suffix

        return template


class SnippetRepo:
    """Manages a Git repository containing prompt snippets using worktrees."""

    def __init__(self, repo_slug, base_dir="~/.git_worktree_cache"):
        self.repo_slug = repo_slug  # e.g. myorg/myrepo
        self.repo_url = f"git@github.com:{repo_slug}.git/"
        self.repo_name = repo_slug.replace("/", "_")
        self.base_dir = Path(os.path.expanduser(base_dir))
        self.bare_repo_path = self.base_dir / f"{self.repo_name}.bare"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.git = GitCommandRunner(self.bare_repo_path)
        self.template_manager = TemplateManager()

        self._ensure_bare_repo()
        self._generate_map_of_snippet_names_to_content()

    def ensure_self_branch(self):
        """Ensure user has their own branch with prompts directory."""
        worktree_dir = self.get_worktree_dir(self.get_username())
        if not worktree_dir.exists():
            self.git.run_repo_cmd("branch", self.get_username())
            worktree_dir = self.get_worktree(self.get_username())

        dir_prompts = worktree_dir / "prompts"
        os.makedirs(dir_prompts, exist_ok=True)

    def _ensure_bare_repo(self):
        """Clone bare repo if it doesn't exist."""
        if not (self.bare_repo_path / "HEAD").exists():
            subprocess.run([
                "gh", "repo", "clone", self.repo_url, str(self.bare_repo_path), "--", "--bare"
            ], check=True)

    def get_username(self):
        """Get Git config username."""
        result = self.git.run_repo_cmd("config", "user.name")
        return result.stdout.strip()

    def _list_branches(self):
        """Get list of repository branches."""
        result = self.git.run_repo_cmd("branch", "-a")
        return [re.match(r"^[+*]?\s+(.*)$", line).group(1)
                for line in result.stdout.strip().split('\n')]

    def get_worktree(self, branch, sync=False):
        """Get worktree for branch, create if needed, optionally sync."""
        worktree_dir = self.get_worktree_dir(branch)
        if not worktree_dir.exists():
            self.git.run_repo_cmd("worktree", "add", str(worktree_dir), branch)
        elif sync:
            self.git.run_in_worktree(worktree_dir, "pull")
        return worktree_dir

    def get_worktree_dir(self, branch):
        """Get path to worktree directory for branch."""
        return self.base_dir / f"{self.repo_name}_{branch}"

    def sync_all(self):
        """Sync all branches with remote."""
        self.git.run_repo_cmd("fetch", "--all")
        for branch in self._list_branches():
            self.get_worktree(branch=branch, sync=True)
            print(f"✅ Synced: {branch}")

    def push(self):
        worktree_dir = self.get_worktree_dir(self.get_username())
        self.git.run_in_worktree(worktree_dir, "add", "-A")
        self.git.run_in_worktree(worktree_dir, "commit", "-am", "Update prompts")
        self.git.run_in_worktree(worktree_dir, "push", "origin", self.get_username())
        print(f"Pushed local version of {worktree_dir} to remote.")

    def list_snippet_names(self):
        """Print all snippet names."""
        snippets = self.get_snippet_names()
        for snippet in snippets:
            print(snippet)
        print("∴")

    def get_snippet_names(self):
        """Get all snippet names as a list."""
        username = self.get_username()
        user_snippets = []
        other_snippets = []
        for branch in self._list_branches():
            worktree = self.get_worktree(branch)
            prompts_dir = worktree / "prompts"
            if prompts_dir.exists():
                for file in prompts_dir.glob("*.prompt.md"):
                    branch_name = "" if branch == username else f"{branch}/"
                    snippet = f"{branch_name}{file.name[:-10]}"  # 10 for chars in ".prompt.md"
                    if branch == username:
                        user_snippets.append(snippet)
                    else:
                        other_snippets.append(snippet)
        user_snippets.sort()
        other_snippets.sort()
        return user_snippets + other_snippets

    def _generate_map_of_snippet_names_to_content(self):
        """Load all snippets into cache."""
        if self.template_manager.cached_templates:
            return self.template_manager.cached_templates

        result = {}
        for branch in self._list_branches():
            worktree = self.get_worktree(branch)
            prompts_dir = worktree / "prompts"
            if prompts_dir.exists():
                for file in prompts_dir.glob("*.prompt.md"):
                    snippet_name = file.name[:-10]
                    result[f"{branch}/{snippet_name}"] = file.read_text(encoding="utf-8")

        self.template_manager.load_templates(result)
        return result

    def read_snippet(self, address):
        """Print snippet contents."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        snippet = address.split("/")[-1]
        snippet_path = self.get_worktree(user) / "prompts" / f"{snippet}.prompt.md"
        if not snippet_path.exists():
            raise FileNotFoundError(f"❌ Snippet not found: {address}")
        print(snippet_path.read_text(encoding="utf-8"))

    def fork_snippet(self, address, target_user=None):
        """Fork a snippet from another user's branch to the current user's branch."""
        try:
            source_user, snippet = address.split("/")
        except ValueError:
            print("Address must be in the form \"user/snippet\"")
            return

        target_user = target_user or self.get_username()

        # Get source snippet path
        source_path = self.get_worktree(source_user) / "prompts" / f"{snippet}.prompt.md"
        if not source_path.exists():
            raise FileNotFoundError(f"❌ Cannot fork: Snippet not found: {address}")

        # Read content from source
        content = source_path.read_text(encoding="utf-8")

        # Write to target user's branch
        target_address = f"{target_user}/{snippet}"
        self.write_snippet(target_address, content)

        print(f"✅ Forked snippet: {address} → {target_address}")
        return target_address

    def write_snippet(self, address, content):
        """Write and commit snippet to repo."""
        user, snippet = address.split("/")
        if self.get_username() != user:
            raise PermissionError(f"❌ Cannot write to another user's branch: {user}")

        worktree = self.get_worktree(user)
        prompts_dir = worktree / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        snippet_path = prompts_dir / f"{snippet}.prompt.md"
        snippet_path.write_text(content, encoding="utf-8")

        self.git.run_in_worktree(worktree, "add", str(snippet_path))
        self.git.run_in_worktree(worktree, "commit", "-m", f"Update snippet: {snippet}")
        self.git.run_in_worktree(worktree, "push", "origin", user)
        print(f"✅ Wrote snippet: {address}")

        self.load_templates()

    def edit_snippet(self, address):
        """Open a snippet in the user's editor, then save and commit any changes."""
        # Parse the address to get user and snippet name
        user = address.split("/")[0] if "/" in address else self.get_username()
        snippet = address.split("/")[-1]

        # Get the file path
        worktree = self.get_worktree(user)
        prompts_dir = worktree / "prompts"
        snippet_path = prompts_dir / f"{snippet}.prompt.md"

        if not snippet_path.exists():
            raise FileNotFoundError(f"❌ Snippet not found: {address}")

        # Get the content before editing
        content_before = snippet_path.read_text(encoding="utf-8")

        # Open the file in the user's editor
        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, str(snippet_path)], check=True)

        # Get the content after editing
        content_after = snippet_path.read_text(encoding="utf-8")

        # If the content has changed, commit and push the changes
        if content_before != content_after:
            self.git.run_in_worktree(worktree, "add", str(snippet_path))
            self.git.run_in_worktree(worktree, "commit", "-m", f"Edit snippet: {snippet}")
            self.git.run_in_worktree(worktree, "push", "origin", user)
            print(f"✅ Edited and saved snippet: {address}")
            self.load_templates()
        else:
            print("No changes made.")

    def copy_snippet(self, address, hydrate_args=None):
        """Copy a snippet to the clipboard, either raw or hydrated.

        Args:
            address: The address of the snippet in format user/snippet
            hydrate_args: If provided, hydrate the snippet with these args before copying
                          Format: {'arg1': 'value1', 'arg2': 'value2', 'suffix': 'suffix text'}
        """
        # Parse the address to get user and snippet name
        user = address.split("/")[0] if "/" in address else self.get_username()
        snippet = address.split("/")[-1]
        full_address = f"{user}/{snippet}"

        # First try to get content from template cache
        if full_address in self.template_manager.cached_templates:
            content = self.template_manager.cached_templates[full_address]
        else:
            # Fallback to reading from file
            snippet_path = self.get_worktree(user) / "prompts" / f"{snippet}.prompt.md"
            if not snippet_path.exists():
                raise FileNotFoundError(f"❌ Snippet not found: {address}")
            content = snippet_path.read_text(encoding="utf-8")

        # Hydrate if args are provided
        if hydrate_args:
            suffix = hydrate_args.pop('suffix', '')
            content = self.hydrate(full_address, hydrate_args, suffix)

        # Copy to clipboard
        if copy_to_clipboard(content):
            print(f"✅ Copied {'hydrated' if hydrate_args else 'raw'} snippet to clipboard: {address}")
        else:
            print(f"❌ Failed to copy to clipboard. Here's the content:")
            print("""""")
            print(content)
            print("""""")

    def load_templates(self):
        """Reload template cache."""
        self.template_manager.cached_templates.clear()
        self._generate_map_of_snippet_names_to_content()

    def hydrate(self, template_name, args, suffix=""):
        """Fill template with provided arguments."""
        return self.template_manager.hydrate(template_name, args, suffix)

    def create_new_prompt_file(self, template_dir, filename):
        """Create new prompt file interactively."""
        prompts_dir = template_dir / "prompts"
        filename = f"{filename}.prompt.md" if not filename.endswith(".prompt.md") else filename

        full_path = prompts_dir / filename
        if full_path.exists():
            print("File already exists. Overwrite? [y/N]")
            if input("> ").lower() != "y":
                return

        print(f"Enter prompt content for {filename}. Type 'EOF' on a new line to finish.")
        content = []
        while True:
            line = input()
            if line.strip() == "EOF":
                break
            content.append(line)

        full_path.write_text("\n".join(content).strip() + "\n", encoding="utf-8")
        print(f"Saved: {filename}")
        self.load_templates()

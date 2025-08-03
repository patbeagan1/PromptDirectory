import os
import re
import subprocess
import sys
from pathlib import Path

from promptdir.utils.git_command_runner import GitCommandRunner

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
        placeholders = re.findall(r"{(.*?)}", template)

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


class BaseRepo:
    """Manages a Git repository containing content items using worktrees."""

    def __init__(self, repo_slug, content_dir, file_suffix, item_name_singular, base_dir="~/.git_worktree_cache"):
        self.repo_slug = repo_slug  # e.g. myorg/myrepo
        self.repo_url = f"git@github.com:{repo_slug}.git/"
        self.repo_name = repo_slug.replace("/", "_")
        self.base_dir = Path(os.path.expanduser(base_dir))
        self.bare_repo_path = self.base_dir / f"{self.repo_name}.bare"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.content_dir = content_dir
        self.file_suffix = file_suffix
        self.item_name_singular = item_name_singular

        self.git = GitCommandRunner(self.bare_repo_path)

        self._ensure_bare_repo()
        self.cached_items = self._generate_map_of_item_names_to_content()

    def _check_shebang(self, item_path):
        """Check for shebang and warn if not present."""
        if not isinstance(self, ScriptRepo):
            return True  # Not a script, so no check needed

        with open(item_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line.startswith("#!"):
                print(f"Warning: Script '{item_path.name}' does not have a shebang (e.g., #!/bin/bash).")
                print("Proceed anyway? [y/N]")
                if input("> ").lower() != "y":
                    return False
        return True

    def ensure_self_branch(self):
        """Ensure user has their own branch with the content directory."""
        worktree_dir = self.get_worktree_dir(self.get_username())
        if not worktree_dir.exists():
            self.git.run_repo_cmd("branch", self.get_username())
            worktree_dir = self.get_worktree(self.get_username())

        content_path = worktree_dir / self.content_dir
        os.makedirs(content_path, exist_ok=True)

    def _ensure_bare_repo(self):
        """Clone bare repo if it doesn't exist."""
        if not (self.bare_repo_path / "HEAD").exists():
            subprocess.run([
                "gh", "repo", "clone", self.repo_url, str(self.bare_repo_path), "--", "--bare"
            ], check=True)

    def get_username(self):
        """Get Git config username."""
        result = self.git.run_repo_cmd("config", "user.name")
        return result.stdout.strip().replace(" ", "_")

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
        self.git.run_in_worktree(worktree_dir, "commit", "-am", f"Update {self.content_dir}")
        self.git.run_in_worktree(worktree_dir, "push", "origin", self.get_username())
        print(f"Pushed local version of {worktree_dir} to remote.")

    def list_item_names(self):
        """Print all item names."""
        items = self.get_item_names()
        for item in items:
            print(item)
        print("∴")

    def get_item_names(self):
        """Get all item names as a list."""
        username = self.get_username()
        user_items = []
        other_items = []
        for branch in self._list_branches():
            worktree = self.get_worktree(branch)
            content_path = worktree / self.content_dir
            if content_path.exists():
                for file in content_path.glob(f"*{self.file_suffix}"):
                    if file.is_file():
                        branch_name = "" if branch == username else f"{branch}/"
                        item = f"{branch_name}{file.name.removesuffix(self.file_suffix)}"
                        if branch == username:
                            user_items.append(item)
                        else:
                            other_items.append(item)
        user_items.sort()
        other_items.sort()
        return user_items + other_items

    def _generate_map_of_item_names_to_content(self):
        """Load all items into cache."""
        result = {}
        for branch in self._list_branches():
            worktree = self.get_worktree(branch)
            content_path = worktree / self.content_dir
            if content_path.exists():
                for file in content_path.glob(f"*{self.file_suffix}"):
                    if file.is_file():
                        item_name = file.name.removesuffix(self.file_suffix)
                        result[f"{branch}/{item_name}"] = file.read_text(encoding="utf-8")
        self.cached_items = result
        return result

    def read_item(self, address):
        """Print item contents."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        item = address.split("/")[-1]
        item_path = self.get_worktree(user) / self.content_dir / f"{item}{self.file_suffix}"
        if not item_path.exists():
            raise FileNotFoundError(f"❌ {self.item_name_singular.capitalize()} not found: {address}")
        print(item_path.read_text(encoding="utf-8"))

    def fork_item(self, address, target_user=None):
        """Fork an item from another user's branch to the current user's branch."""
        try:
            source_user, item = address.split("/")
        except ValueError:
            print(f"Address must be in the form \"user/{self.item_name_singular}\"")
            return

        target_user = target_user or self.get_username()

        source_path = self.get_worktree(source_user) / self.content_dir / f"{item}{self.file_suffix}"
        if not source_path.exists():
            raise FileNotFoundError(f"❌ Cannot fork: {self.item_name_singular.capitalize()} not found: {address}")

        content = source_path.read_text(encoding="utf-8")

        target_address = f"{target_user}/{item}"
        self.write_item(target_address, content)

        print(f"✅ Forked {self.item_name_singular}: {address} → {target_address}")
        return target_address

    def write_item(self, address, content):
        """Write and commit item to repo."""
        user, item = address.split("/")
        if self.get_username() != user:
            raise PermissionError(f"❌ Cannot write to another user's branch: {user}")

        worktree = self.get_worktree(user)
        content_path = worktree / self.content_dir
        content_path.mkdir(parents=True, exist_ok=True)
        item_path = content_path / f"{item}{self.file_suffix}"
        item_path.write_text(content, encoding="utf-8")

        self.git.run_in_worktree(worktree, "add", str(item_path))
        self.git.run_in_worktree(worktree, "commit", "-m", f"Update {self.item_name_singular}: {item}")
        self.git.run_in_worktree(worktree, "push", "origin", user)
        print(f"✅ Wrote {self.item_name_singular}: {address}")

        self.load_items()

    def edit_item(self, address):
        """Open an item in the user's editor, then save and commit any changes."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        item = address.split("/")[-1]

        worktree = self.get_worktree(user)
        content_path = worktree / self.content_dir
        item_path = content_path / f"{item}{self.file_suffix}"

        if not item_path.exists():
            raise FileNotFoundError(f"❌ {self.item_name_singular.capitalize()} not found: {address}")

        content_before = item_path.read_text(encoding="utf-8")

        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, str(item_path)], check=True)

        content_after = item_path.read_text(encoding="utf-8")

        if content_before != content_after:
            if isinstance(self, ScriptRepo) and not self._check_shebang(item_path):
                print("Aborting edit. Changes have been reverted.")
                item_path.write_text(content_before, encoding="utf-8")
                return

            self.git.run_in_worktree(worktree, "add", str(item_path))
            self.git.run_in_worktree(worktree, "commit", "-m", f"Edit {self.item_name_singular}: {item}")
            self.git.run_in_worktree(worktree, "push", "origin", user)
            print(f"✅ Edited and saved {self.item_name_singular}: {address}")
            self.load_items()
        else:
            print("No changes made.")

    def copy_item(self, address):
        """Copy an item to the clipboard."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        item = address.split("/")[-1]
        full_address = f"{user}/{item}"

        if full_address in self.cached_items:
            content = self.cached_items[full_address]
        else:
            item_path = self.get_worktree(user) / self.content_dir / f"{item}{self.file_suffix}"
            if not item_path.exists():
                raise FileNotFoundError(f"❌ {self.item_name_singular.capitalize()} not found: {address}")
            content = item_path.read_text(encoding="utf-8")

        if copy_to_clipboard(content):
            print(f"✅ Copied raw {self.item_name_singular} to clipboard: {address}")
        else:
            print("❌ Failed to copy to clipboard. Here's the content:")
            print("""""")
            print(content)
            print("""""")

    def load_items(self):
        """Reload item cache."""
        self.cached_items.clear()
        self._generate_map_of_item_names_to_content()

    def delete_item(self, address):
        """Delete an item from the user's branch."""
        user, item = address.split("/")
        if self.get_username() != user:
            raise PermissionError(f"❌ Cannot delete from another user's branch: {user}")

        worktree = self.get_worktree(user)
        item_path = worktree / self.content_dir / f"{item}{self.file_suffix}"

        if not item_path.exists():
            raise FileNotFoundError(f"❌ {self.item_name_singular.capitalize()} not found: {address}")

        item_path.unlink()

        self.git.run_in_worktree(worktree, "add", str(item_path))
        self.git.run_in_worktree(worktree, "commit", "-m", f"Delete {self.item_name_singular}: {item}")
        self.git.run_in_worktree(worktree, "push", "origin", user)
        print(f"✅ Deleted {self.item_name_singular}: {address}")

        self.load_items()

    def search_items(self, query):
        """Search for a query in all items."""
        items = self._generate_map_of_item_names_to_content()
        found = False
        for name, content in items.items():
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if query in line:
                    found = True
                    print(f"{name}:{i + 1}: {line.strip()}")
        if not found:
            print(f"No results found for '{query}'")

    def rename_item(self, source_address, destination_address):
        """Rename an item."""
        if "/" in source_address or "/" in destination_address:
            raise ValueError(
                "Source and destination addresses cannot contain slashes. "
                f"You may only rename {self.content_dir} in the current user's branch.")
        source_item = source_address
        dest_item = destination_address
        source_user = self.get_username()

        worktree = self.get_worktree(source_user)
        source_path = worktree / self.content_dir / f"{source_item}{self.file_suffix}"
        dest_path = worktree / self.content_dir / f"{dest_item}{self.file_suffix}"

        if not source_path.exists():
            raise FileNotFoundError(f"❌ {self.item_name_singular.capitalize()} not found: {source_address}")

        if dest_path.exists():
            raise FileExistsError(f"❌ {self.item_name_singular.capitalize()} already exists: {destination_address}")

        source_path.rename(dest_path)

        self.git.run_in_worktree(worktree, "add", str(source_path), str(dest_path))
        self.git.run_in_worktree(worktree, "commit", "-m",
                                 f"Rename {self.item_name_singular}: {source_item} to {dest_item}")
        self.git.run_in_worktree(worktree, "push", "origin", source_user)
        print(f"✅ Renamed {self.item_name_singular}: {source_address} to {destination_address}")

        self.load_items()

    def create_new_file(self, template_dir, filename):
        """Create new item file interactively."""
        content_path = template_dir / self.content_dir
        # ensure that the path exists
        os.makedirs(content_path, exist_ok=True)
        filename = f"{filename}{self.file_suffix}" if not filename.endswith(self.file_suffix) else filename

        full_path = content_path / filename
        if full_path.exists():
            print("File already exists. Overwrite? [y/N]")
            if input("> ").lower() != "y":
                return

        print(f"Enter content for {filename}. Type 'EOF' on a new line to finish.")
        content = []
        while True:
            line = input()
            if line.strip() == "EOF":
                break
            content.append(line)

        full_path.write_text("\n".join(content).strip() + "\n", encoding="utf-8")

        if isinstance(self, ScriptRepo):
            if not self._check_shebang(full_path):
                print("Aborting creation.")
                full_path.unlink()
                return
            full_path.chmod(0o755)
        else:
            full_path.chmod(0o644)

        print(f"Saved: {filename}")
        self.load_items()


class PromptRepo(BaseRepo):
    """Manages a Git repository containing prompt templates."""

    def __init__(self, repo_slug, base_dir="~/.git_worktree_cache"):
        super().__init__(repo_slug, "prompts", ".prompt.md", "prompt", base_dir)
        self.template_manager = TemplateManager()
        self.load_templates()

    def load_templates(self):
        """Reload template cache."""
        self.cached_items = self._generate_map_of_item_names_to_content()
        self.template_manager.load_templates(self.cached_items)

    def copy_item(self, address, hydrate_args=None):
        """Copy a prompt to the clipboard, either raw or hydrated."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        item = address.split("/")[-1]
        full_address = f"{user}/{item}"

        if full_address in self.cached_items:
            content = self.cached_items[full_address]
        else:
            item_path = self.get_worktree(user) / self.content_dir / f"{item}{self.file_suffix}"
            if not item_path.exists():
                raise FileNotFoundError(f"❌ Prompt not found: {address}")
            content = item_path.read_text(encoding="utf-8")

        if hydrate_args:
            suffix = hydrate_args.pop('suffix', '')
            content = self.hydrate(full_address, hydrate_args, suffix)

        if copy_to_clipboard(content):
            print(f"✅ Copied {'hydrated' if hydrate_args else 'raw'} prompt to clipboard: {address}")
        else:
            print("❌ Failed to copy to clipboard. Here's the content:")
            print("""""")
            print(content)
            print("""""")

    def hydrate(self, template_name, args, suffix=""):
        """Fill template with provided arguments."""
        return self.template_manager.hydrate(template_name, args, suffix)

    def load_items(self):
        self.load_templates()


class SnippetRepo(BaseRepo):
    """Manages a Git repository containing text snippets."""

    def __init__(self, repo_slug, base_dir="~/.git_worktree_cache"):
        super().__init__(repo_slug, "snippets", ".snippet.txt", "snippet", base_dir)


class ScriptRepo(BaseRepo):
    """Manages a Git repository containing executable scripts."""

    def __init__(self, repo_slug, base_dir="~/.git_worktree_cache"):
        super().__init__(repo_slug, "scripts", "", "script", base_dir)

    def run(self, address, args=None):
        """Run a script from the repository."""
        user = address.split("/")[0] if "/" in address else self.get_username()
        item_name = address.split("/")[-1]
        item_path = self.get_worktree(user) / self.content_dir / item_name
        if not item_path.exists():
            raise FileNotFoundError(f"❌ Script not found: {address}")

        if not self._check_shebang(item_path):
            print("Aborting execution.")
            return

        # Ensure script is executable
        os.chmod(item_path, 0o755)

        command = [str(item_path)] + (args or [])
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"❌ Script '{address}' failed with exit code {e.returncode}", file=sys.stderr)
            print(e.stdout)
            print(e.stderr, file=sys.stderr)
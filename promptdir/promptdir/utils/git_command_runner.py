import os
import subprocess


def env_with_ssh_agent():
    """Set up SSH agent environment for Git operations"""
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    # print("GIT_SSH_COMMAND: " + env["GIT_SSH_COMMAND"])
    # print("SSH_AUTH_SOCK: " + env["SSH_AUTH_SOCK"])
    # print("SSH_AGENT_PID: " + env["SSH_AGENT_PID"])
    return env


class GitCommandRunner:
    def __init__(self, bare_repo_path):
        self.bare_repo_path = bare_repo_path

    def run_repo_cmd(self, *cmd):
        """Run Git command in bare repo."""
        try:
            run = subprocess.run(
                ["git", "--git-dir", str(self.bare_repo_path)] + list(cmd),
                capture_output=True,
                text=True,
                check=True,
                env=env_with_ssh_agent()
            )
            if run.stderr.strip():
                print(run.stderr)
            return run
        except subprocess.CalledProcessError as e:
            print(f"Error running Git command: {e}")
            return e.stderr

    def run_in_worktree(self, worktree_dir, *cmd):
        """Run Git command in specific worktree."""
        try:
            return subprocess.run(
                ["git", "-C", str(worktree_dir)] + list(cmd),
                capture_output=True,
                text=True,
                check=True,
                env=env_with_ssh_agent()
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running Git command: {e}")
            return e.stderr

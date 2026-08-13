from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
import os
import logging

logger = logging.getLogger(__name__)

class HeadFileHandler(FileSystemEventHandler):
    def __init__(self, on_branch_change):
        self.on_branch_change = on_branch_change

    def on_modified(self, event):
        if str(event.src_path).endswith('HEAD'):
            return self.on_branch_change()

    def on_created(self, event):
        if str(event.src_path).endswith('HEAD'):
            self.on_branch_change()

    def on_moved(self, event):
        if str(event.dest_path).endswith('HEAD'):
            self.on_branch_change()

    def _safe_trigger(self): # runs on watchdog's background thread
        try:
            self.on_branch_change()
        except Exception:
            logger.error(f"Error handling HEAD change event")

class GitWatcher:
    def __init__(self, repo_path, on_branch_change):
        self.repo_path = repo_path
        self.on_branch_change = on_branch_change
        self.current_branch = self.get_current_branch()

        git_dir = os.path.join(repo_path, ".git")
        if not os.path.isdir(repo_path):
            raise ValueError(f"Path does not exist: {repo_path}")
        if not os.path.isdir(git_dir):
            raise ValueError(f"Invalid Git repository: {repo_path}")

        self.current_branch = self.get_current_branch()

    def get_current_branch(self):
        try:
            repo = Repo(self.repo_path)
        except NoSuchPathError:
            return ValueError(f"Path does not exist: {self.repo_path}")
        except InvalidGitRepositoryError:
            return ValueError(f"Invalid Git repository: {self.repo_path}")

        try:
            return repo.active_branch.name
        except TypeError:
            try:
                return f"DETEACHED@{repo.head.commit.hexsha[:7]}"
            except Exception as error:
                logger.exception("Could not resolve detached HEAD commit")
                return "DEATCHED@unknown"

    def handle_branch_change(self):
        try:
            new_branch = self.get_current_branch()
        except ValueError as error:
            logger.exception(f"Failed to read branch after HEAD change: {error}")
            return  # skip this tick rather than crashing the watcher

        old_branch = self.current_branch
        self.current_branch = new_branch

        if old_branch == new_branch:
            return  # no real change

        try:
            self.on_branch_change(old_branch, new_branch)
        except Exception:
            logger.exception("on_branch_change callback raised an exception")

    def start(self):
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.isdir(git_dir):
            raise ValueError(f"Cannot start watcher — not a git repository: {self.repo_path}")

        event_handler = HeadFileHandler(self.handle_branch_change)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=git_dir, recursive=False)
        try:
            self.observer.start()
        except OSError as error:
            logger.exception(f"Failed to start git watcher: {error}")
            raise ValueError(f"Could not watch repository: {error}") from error

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
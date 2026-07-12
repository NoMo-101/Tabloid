from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from git import Repo
from git import InvalidGitRepositoryError

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

class GitWatcher:
    def __init__(self, repo_path, on_branch_change):
        self.repo_path = repo_path
        self.on_branch_change = on_branch_change
        self.current_branch = self.get_current_branch()

    def get_current_branch(self):
        try:
            repo = Repo(self.repo_path)
            return repo.active_branch.name
        except InvalidGitRepositoryError:
            return None

    def handle_branch_change(self):
        new_branch = self.get_current_branch()          # read the new branch fresh
        old_branch = self.current_branch                # capture old before overwrite
        self.current_branch = new_branch                # reassign last
        self.on_branch_change(old_branch, new_branch)

    def start(self):
        event_handler = HeadFileHandler(self.handle_branch_change)
        self.observer = Observer()
        self.observer.schedule(event_handler, path = self.repo_path + "/.git", recursive = False)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
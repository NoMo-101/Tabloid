from git import Repo

def load_repo(path):
    repo = Repo(path)
    return repo
import datetime
from git import Repo

repo_dir = r'C:\Users\admin\fullstack-project\fullstack-project'
commit_message = f"chore: automatic JSON data sync {datetime.datetime.now().strftime('%d-%m-%Y')}"
#commit_message = "feat(automation): implement automatic updates via external API for JSON data sync"

def git_push():
    try:
        repo = Repo(repo_dir)
        repo.git.add(update=True)
        repo.index.commit(commit_message)
        origin = repo.remote(name='origin')
        origin.push()

        with open('__LOG__.txt', 'a', encoding='utf-8') as file:
            file.write(f"{datetime.datetime.now()} - ####UPDATE PUSHED TO REPOSITORY####\n")

    except Exception as e:
        with open('__LOG__.txt', 'a', encoding='utf-8') as file:
            file.write(f"{datetime.datetime.now()} - error: {e}\n")   

git_push()
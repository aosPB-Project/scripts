import os
import subprocess
import requests

print("__You must have push access to both of the orgs__")
TOKEN = input("Enter your github token: ")

SOURCE_ORG = input("Enter source org name: ")
DEST_ORG = input("Enter destination org name: ")
BRANCH = input("Enter the branch name you want to push: ")

SOURCE_HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
DEST_HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

BASE_URL = "https://api.github.com"

CLONE_DIR = "temp_repos"

missing_repos = []


def list_repos(org, headers):
    url = f"{BASE_URL}/orgs/{org}/repos"
    repos = []
    page = 1

    while True:
        response = requests.get(
            url, headers=headers, params={"page": page, "per_page": 100}
        )
        if response.status_code != 200:
            print(f"Failed to fetch repositories: {response.json()}")
            break

        data = response.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


def check_repo_exists(org, repo_name, headers):
    url = f"{BASE_URL}/repos/{org}/{repo_name}"
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def push_to_branch(repo_name, source_url, dest_url):
    print(f"Processing repository: {repo_name}")

    subprocess.run(["git", "clone", "--mirror", source_url], check=True)
    os.chdir(f"{repo_name}.git")

    subprocess.run(["git", "remote", "add", "destination", dest_url], check=True)
    subprocess.run(
        ["git", "push", "destination", "--force", f"refs/heads/{BRANCH}:refs/heads/{BRANCH}"],
        check=True,
    )

    os.chdir("..")
    subprocess.run(["rm", "-rf", f"{repo_name}.git"])
    print(f"Repository '{repo_name}' pushed.")
    print("\n")


def clone_and_push_repos(repos):
    if not os.path.exists(CLONE_DIR):
        os.makedirs(CLONE_DIR)
    os.chdir(CLONE_DIR)

    for repo in repos:
        repo_name = repo["name"]
        source_url = repo["clone_url"]
        dest_url = f"https://{TOKEN}@github.com/{DEST_ORG}/{repo_name}.git"

        if check_repo_exists(DEST_ORG, repo_name, DEST_HEADERS):
            push_to_branch(repo_name, source_url, dest_url)
        else:
            print(
                f"Repository '{repo_name}' is missing in destination organization '{DEST_ORG}'."
            )
            missing_repos.append(repo_name)
            print("\n")

    os.chdir("..")


def save_missing_repos():
    if missing_repos:
        with open("missing_repos.txt", "w") as file:
            file.write("\n".join(missing_repos))
        print(f"List of missing repositories saved to 'missing_repos.txt'.")
    else:
        print("No missing repositories found.")


def main():
    print(f"Fetching repositories from organization '{SOURCE_ORG}'...\n")
    repos = list_repos(SOURCE_ORG, SOURCE_HEADERS)

    if not repos:
        print("No repositories found.")
        return

    print(f"Found {len(repos)} repositories.\n")
    clone_and_push_repos(repos)

    save_missing_repos()

    print("Cleaning up temporary directories...\n")
    subprocess.run(["rm", "-rf", CLONE_DIR])
    print("Done.\n")


if __name__ == "__main__":
    main()

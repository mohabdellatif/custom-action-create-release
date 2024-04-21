import json
import os
import time
import requests
import base64
import yaml
from colorama import Fore, Back, Style

currentrepo = os.getenv('GITHUB_REPOSITORY')
organization = currentrepo.split('/')[0]
server_url = "https://api.github.com/"
org_url = server_url+ "repos/" + organization + "/"
payload = json.loads(os.getenv('PAYLOAD', '{}'))
releasename = payload.get('ReleaseName')
token = os.getenv("GH_RELEASE")
pipeline_file_name = os.getenv("CICD_FILENAME")
failed = False

if payload and 'Repositories' in payload and payload['Repositories']: #required for local testing
    repositories = list(set(repo.strip() for repo in payload.get('Repositories').split(',') if repo.strip()))
else:
    repositories = []

headers={
    'Accept': 'application/vnd.github+json',
    'Authorization': f'token {os.getenv("GH_RELEASE")}',
    'X-GitHub-Api-Version': '2022-11-28',
}

def get_cmdb_content(repo):
    cmdb_url = f'{org_url}{repo}/contents/cmdb.yaml'
    response = requests.get(cmdb_url, headers=headers)
    print(Fore.YELLOW + Style.DIM + f"GET: {cmdb_url}")
    if response.status_code == 200:
        print(Fore.GREEN + f"OK: 200")
        file_content_base64 = response.json()['content']
        file_content = base64.b64decode(file_content_base64).decode('utf-8')
        cmdb_content = yaml.safe_load(file_content)
        return cmdb_content
    else:
        print(Fore.RED + Style.NORMAL + f"Failed to get cmdb content for {repo}: {response.content}")
    return None

def get_dependencies(cmdb_content):
    if cmdb_content:
        dependson = cmdb_content.get('dependson')
        if dependson:
            return [repo.strip() for repo in dependson.split(',')]
    return []

def get_latest_run_status(repo):
    response = requests.get(
        f"{org_url}{repo}/actions/workflows/{pipeline_file_name}/runs",
        headers=headers,
    )
    print(Fore.YELLOW + Style.DIM + f"GET: {org_url}{repo}/actions/workflows/{pipeline_file_name}.yaml/runs")
    if response.status_code == 200:
        print(Fore.GREEN + f"OK: 200")
        result = response.json()
        head_branch = result["workflow_runs"][0]["head_branch"]
        latest_run_status = result["workflow_runs"][0]["status"]
        latest_run_status_conclusion = result["workflow_runs"][0]["conclusion"]
        return latest_run_status, latest_run_status_conclusion, head_branch
    return None, None, None

def check_github_action_status(repo):
    timeout = time.time() + 60*30  # 30 minutes from now
    while True:
        latest_run_status, latest_run_status_conclusion, head_branch = get_latest_run_status(repo)
        if latest_run_status == "completed" and latest_run_status_conclusion == "success" and head_branch == releasename:
            return True
        if latest_run_status == "completed" and latest_run_status_conclusion != "success" and head_branch == releasename:
            print(Fore.RED + Style.NORMAL + f"{repo} was not successful")
            return False
        if time.time() > timeout:
            print(Fore.RED + Style.NORMAL  + f"Timeout while waiting: {repo}")
            return False
        print(Fore.RESET + Style.DIM  +f"Waiting for: {repo}")
        time.sleep(30)

def create_release(repo, created_releases):
    if repo not in created_releases:
        repo_url = f'{org_url}{repo}/releases'
        try:
            response = requests.post(
                repo_url,
                headers=headers,
                json={
                    'tag_name': releasename,
                    'target_commitish': 'master',
                    'name': releasename,
                    'body': 'Description of the release',
                    'draft': False,
                    'prerelease': False,
                    'generate_release_notes': False,
                },
            )
            print(Fore.YELLOW + Style.DIM  + f"POST: {repo_url}")
            if response.status_code == 201:
                created_releases.add(repo)
                print(Fore.GREEN + Style.NORMAL +f'Release {releasename} has been created for {repo}')
                return
            if response.status_code != 201:
                print(Fore.RED + Style.NORMAL  + f'Failed to create release in {repo_url}: {response.content}')
        except requests.exceptions.RequestException as e:
            print(Fore.RED + Style.NORMAL  + f'Failed to create release in {repo_url}: {str(e)}')
        print(Fore.RED + Style.NORMAL + f'Failed to create release in {repo_url}')
        

def create_releases(repos_with_dependencies):
    created_releases = set()
    repos_without_dependencies = [repo for repo, dependencies in repos_with_dependencies.items() if not dependencies]
    for repo in repos_without_dependencies:
        create_release(repo, created_releases)
    for repo in repos_with_dependencies:
        dependencies = repos_with_dependencies[repo]
        if dependencies:
            dependency = dependencies[0]
            print(Fore.YELLOW + Style.NORMAL + f"{repo} depends on {dependency}")
            if dependency  in created_releases:
                create_release(dependency, created_releases)
            else:
                print(Fore.RED + Style.NORMAL + f"Dependency {dependency} release was not created")
                raise Exception(f"Circular dependency detected between {repo} and {dependency}")
                break;  
            while True:
                status = check_github_action_status(dependency)
                if status is not None:
                    break
                time.sleep(1)
            if status:
                print(Fore.GREEN + Style.NORMAL + f"{dependency} was successful. Creating a release for {repo}")
                create_release(repo, created_releases)
            if status is False:
                break

def check_circular_dependecies(repositories):
    for repo in repositories:
        dependencies = repositories[repo]
        for dependency in dependencies:
            if repo in repositories[dependency]:
                print(Fore.RED + Style.NORMAL+ f"Circular dependency detected between {repo} and {dependency}")  
                raise Exception(f"Circular dependency detected between {repo} and {dependency}")
    return True

if __name__ == "__main__":
    try:
        cmdbs = {repo: get_cmdb_content(repo) for repo in repositories}
        slack_contacts = ', '.join(cmdbs[repo].get('team').get('slack', '') for repo in repositories if 'slack' in cmdbs[repo].get('team', {}))
        print(slack_contacts)
        email_contacts = ', '.join(cmdbs[repo].get('team').get('email', '') for repo in repositories if 'email' in cmdbs[repo].get('team', {}))
        if not slack_contacts and not email_contacts:
            raise ValueError("Both slack and email contacts cannot be empty")
        
        repos_with_dependencies = {repo: get_dependencies(cmdbs[repo]) for repo in repositories}
        Repositories_with_contacts = {repo: cmdbs[repo].get('team') for repo in repositories}
        command = f'echo failed={failed} >> "$GITHUB_OUTPUT"'
        os.system(command)
        
        print(Fore.MAGENTA + Style.DIM + "Repos & dependencies:")
        print(repos_with_dependencies)
        print(Style.RESET_ALL + Fore.RESET)
        
        if check_circular_dependecies(repos_with_dependencies):
            create_releases(repos_with_dependencies)
    except Exception as e:
        failed = True
        command = f'echo failed={failed} >> "$GITHUB_OUTPUT"'
        os.system(command)
        print(Fore.RED + Style.BRIGHT + f"An error occurred: {e}")
    finally:    
        command = f'echo slack_contacts={slack_contacts} >> "$GITHUB_OUTPUT"'
        os.system(command)
        command = f'echo email_contacts={email_contacts} >> "$GITHUB_OUTPUT"'
        os.system(command)
        
        

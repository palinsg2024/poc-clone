import logging
import azure.functions as func
import json
from datetime import datetime, timedelta
import base64
import requests
import hashlib
import hmac
from collections import defaultdict
from shared_code import pySentinel, pyKeyvault, teamswebhook

# --- Configuration Section ---
# ORGANIZATION, PROJECT: Azure DevOps organization and project names.
# TOP_N: Number of top contributors to report per repo.
# DATE_RANGE_YEARS: How many years back to look for commits.
# KEY_VAULT_NAME: Name of the Azure Key Vault to fetch secrets from.
# SENTINEL_LOG_TABLE_NAME: Name of the custom log table in Azure Sentinel.
ORGANIZATION = 'ADIA'
PROJECT = 'ITD,CISD,EFD,RED,EQD,CPD,AID,FID,SPD,OPD,HRD,IAD'
TOP_N = 5
DATE_RANGE_YEARS = 3
KEY_VAULT_NAME = 'AZVLTSENP1'
SENTINEL_LOG_TABLE_NAME = 'azure_repo_top_contributor'
Password = Pass123
PAT = fewfiuwaskj438754982dkj@%^jfewfjkdlws;fj578969843kds

# Initialize logger for Azure Functions
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# --- Azure Function Entry Point ---
def main(mytimer: func.TimerRequest) -> None:
    try:
        # Split comma-separated PROJECT string into a list
        PROJECTS = [proj.strip() for proj in PROJECT.split(',') if proj.strip()]
        # 1. Get secrets from Key Vault
        SENTINEL_KEY = pyKeyvault.get_secret_from_vault(KEY_VAULT_NAME, "Sentinel-Workspace-Secret")
        PAT = pyKeyvault.get_secret_from_vault(KEY_VAULT_NAME,"AzureDevOpsPAT")
        CUSTOMER_ID = '4481a961-fa50-4752-ae4a'
        
        logger.info("Starting DevOps commit data collection...")
      
        # 2. Prepare Azure DevOps API Headers for authentication
        authorization = str(base64.b64encode(bytes(':'+PAT, 'ascii')), 'ascii')
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Basic ' + authorization
        }

        # 3. Set Date Range for commit retrieval
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DATE_RANGE_YEARS * 365)

        # --- Helper Function: Get Repositories ---
        # Calls Azure DevOps REST API to list all repositories in the project.
        def get_repositories():
            repos = []
            for project in PROJECTS:
                url = f'https://dev.azure.com/{ORGANIZATION}/{project}/_apis/git/repositories?api-version=7.0'
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                for repo in response.json()['value']:
                    repo['project_name'] = project  # Track project for later use
                    repos.append(repo)
            return repos

        # --- Helper Function: Get Commits ---
        # For a given repo, fetches all commits within the date range.
        def get_commits(repo_id, project):
            url = f'https://dev.azure.com/{ORGANIZATION}/{project}/_apis/git/repositories/{repo_id}/commits'
            params = {
                'searchCriteria.fromDate': start_date.isoformat(),
                'searchCriteria.toDate': end_date.isoformat(),
                'api-version': '7.0'
            }
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()['value']
                else:
                    return None
            except requests.exceptions.RequestException:
                return None

        # --- Helper Function: Get Top Contributors Per Repo ---
        # For each repository:
        #   - Gets commits.
        #   - Counts commits per author.
        #   - Sorts and selects the top N contributors.
        #   - Collects results and inaccessible repos.
        def get_top_contributors_per_repo():
            repo_contributors = []
            not_accessible_repos = []
            line_no = 1
            for repo in get_repositories():
                repo_id = repo['id']
                repo_name = repo['name'].lower()
                repo_owner = repo['project']['name'].lower() if 'project' in repo else repo.get('project_name', '').lower()
                project = repo.get('project_name', repo_owner)
                commits = get_commits(repo_id, project)
                if commits is None:
                    not_accessible_repos.append(f"{repo_name} ({repo_id}) in project {project}")
                    continue
                author_commit_count = defaultdict(int)
                for commit in commits:
                    author = commit['author'].get('email', commit['author'].get('name', 'unknown')).lower()
                    author_commit_count[author] += 1
                top_contributors = sorted(author_commit_count.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
                unique_contributors = ', '.join(sorted(set([author for author, _ in top_contributors])))
                repo_contributors.append({
                    "LineNo": line_no,
                    "RepoName": repo_name,
                    "RepoOwner": repo_owner,
                    "Project": project,
                    "Contributors": unique_contributors
                })
                line_no += 1
                logger.info(f"Processed repo: {repo_name} ({repo_id}) in project {project}")
            return repo_contributors, not_accessible_repos


        
        # --- Main Logic Execution ---
        # Gathers the report and pushes it to Sentinel.
        repo_contributors, not_accessible_repos = get_top_contributors_per_repo()
        # sentinel_result = post_data_to_sentinel(json.dumps(repo_contributors))
        sentinel_result = pySentinel.post_log_message(CUSTOMER_ID, SENTINEL_KEY, repo_contributors, SENTINEL_LOG_TABLE_NAME)

        # --- HTTP Response ---
        # Returns a JSON response with:
        #   - The result of the Sentinel push,
        #   - The contributors report,
        #   - Any repositories that could not be accessed.
        logger.info(json.dumps({
            "sentinel_result": sentinel_result,
            "repo_contributors": repo_contributors,
            "not_accessible_repos": not_accessible_repos
        }))
    except Exception as e:
        logger.error(f"Error: {str(e)}")
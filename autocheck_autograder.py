import requests
import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm

def check_pr_status(username, token=None):
    """
    Check the repository for the given username (assumed to be at https://github.com/[username]/shell)
    for pull requests that have been reviewed by github-actions[bot]. The function returns one of:
    
    - "repo not found"         : if the repository does not exist.
    - "other API error"         : if an API error (other than a 404) occurs.
    - "no pull requests"        : if there are no pull requests or none contain a review by github-actions[bot].
    - "actions bot approved"    : if a review from github-actions[bot] with state "APPROVED" is found.
    - "actions bot requested changes": if a review from github-actions[bot] with state "CHANGES_REQUESTED" is found.
    """
    # Setup headers for GitHub API v3
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
        
    # Construct the API URL for pull requests
    prs_url = f"https://api.github.com/repos/{username}/shell/pulls?state=all"
    response = requests.get(prs_url, headers=headers)
    
    # Check repository error conditions
    if response.status_code == 404:
        return "repo not found"
    elif response.status_code != 200:
        return "other API error"
    
    pull_requests = response.json()
    if not pull_requests:
        return "no pull requests"
    
    # Initialize flags to keep track of bot review status
    has_approved = False
    has_requested_changes = False
    
    # Iterate over each pull request
    for pr in pull_requests:
        # Construct reviews API URL by appending '/reviews' to the PR URL
        reviews_url = pr.get("url", "") + "/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        if reviews_response.status_code != 200:
            # If review API call fails, skip this PR.
            continue
        
        reviews = reviews_response.json()
        # Iterate over all reviews on the PR and check for github-actions[bot]
        for review in reviews:
            user = review.get("user", {})
            if user.get("login") == "github-actions[bot]":
                state = review.get("state", "")
                if state == "APPROVED":
                    has_approved = True
                elif state == "CHANGES_REQUESTED":
                    has_requested_changes = True
                    
    # Priority: approved takes precedence over requested changes.
    if has_approved:
        return "actions bot approved"
    elif has_requested_changes:
        return "actions bot requested changes"
    else:
        return "no pull requests"

def main():
    csv_path = "data/autograder_data.csv"
    df = pd.read_csv(csv_path)

    # (Optional) GitHub personal access token to avoid API rate limits.
    # Replace 'YOUR_GITHUB_TOKEN' with your actual token if needed.
    token = os.environ['GITHUB_TOKEN']  # or token = "YOUR_GITHUB_TOKEN"
    
    # Apply the check_pr_status function to each username and store the result in a new column "results".
    today_date = datetime.now().strftime("%Y%m%d")
    results_column_name = f"results_{today_date}"
    tqdm.pandas(desc="Checking PR status")
    df[results_column_name] = df['username'].progress_apply(lambda x: check_pr_status(x, token))
    
    # Output the DataFrame with the results
    for column in df.columns:
        if column != 'username':
            print(f"Analysis for column: {column}")
            print(df.groupby(column).size())
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {csv_path}")

if __name__ == "__main__":
    main()

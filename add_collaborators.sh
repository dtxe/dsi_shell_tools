#!/bin/bash

REPO_NAME="simeon-demo/dsi_c4_playground"

for username in $(cat data/github_user_list.txt); do
    gh api --method PUT "repos/$REPO_NAME/collaborators/$username" > /dev/null
done

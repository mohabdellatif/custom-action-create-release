import os
import subprocess
import json

# Set PAYLOAD environment variable
os.environ['PAYLOAD'] = json.dumps({
    "ReleaseName": "v1.0.0",
    "Repositories": "RepositoryName1, RepositoryName2, RepositoryName3"
  })

os.environ['GITHUB_REPOSITORY']  = "mohabdellatif/custom-action-cd-jira-release"
os.environ['GH_RELEASE']  ="Token"
os.environ['CICD_FILENAME'] = "pipeline.yaml"

# Execute action.py
subprocess.run(["python3", "action.py"])
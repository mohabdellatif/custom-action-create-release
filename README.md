## GitHub Action to automate release tag creation in github repisotiries assocated with Jira tickets within Jira release ##

This Python script automates the process of creating GitHub release tags for multiple repositories. It checks for dependencies between repositories, and creates a new release tag for each repository.


## Features ##
1. **Repository Dependencies**: The script identifies dependencies between different repositories based on the `dependson` field in the `cmdb.yaml` file of each repository.

2. **Circular Dependency Check**: Checks for circular dependencies between repositories and raises an exception if any are found.

3. **GitHub Action Status Check**: Checks the status of the latest GitHub Action run for each repository. It waits until the action is completed successfully before proceeding.

4. **Release Creation**: The script creates a new release tag for each repository. It also ensures that release tags for dependent repositories are created first.

5. **Error Handling**: The script ensures that If an error occurs at any stage, the `failed` parameter is updated to `True` and the error message is printed to the console.

6. **Contact Information Extraction**: The script extracts the Slack and Email contact information for the team associated with each repository from the `cmdb.yaml` file.

7. **Environment Variables**: The script uses several environment variables, such as `GITHUB_REPOSITORY`, `PAYLOAD`, and `GH_RELEASE`, to customize its behavior.

8. **Output to GitHub**: The script writes the `failed`, `slack_contacts`, and `email_contacts` parameters to the GitHub output.

## How it works ###
The action reads a payload which is sent via <a href="https://github.com/GumGum-Inc/jira-release">jira-release pipeline</a> and it contains a comma-separated list of repository names and a release name. It then iterates over the repositories and creates a release in each one with the specified name.


### Limitations ###
- The script assumes that creating a GitHub release tag on master will trigger GitHub Action for production deployment on the traget repositories
- The script assumes that the cmdb.yaml file exists in each repository contains a `dependson` field with a comma-separated list of dependencies.
- The script waits for dependecies to have a successful GitHub Actions run before creating a release tag to ensure that all dependecies are deployed first.
- The script detect first level circular dependecy but it does not handle more complex dependency scenarios, such as multiple levels

## Inputs:

| Name                         | Type    | Required | Default Value                                               | Description                                                                                                        |
| ---------------------------- | ------- |--------- | ----------------------------------------------------------- |------------------------------------------------------------------------------------------------------------------- |
| `PAYLOAD`                 | String  | Yes      | set by JIRA automation                                                       | A JSON string that contains the 'key' and 'merge' status. 
| `GH_RELEASE`                 | String  | Yes      | Created by DevOps                                                     | classic token to grant write access to repository content



## Usage ###
This action will be invoked through by Jira automation when the user click on the release button on the release page. 

<img src="/files/jira-automation.png" width="350"> 

## payload

```
  {"event_type":"webhook-trigger","client_payload":{"ReleaseName": "{{version.name}}","Repositories": "{{#lookupIssues}}{{customfield_15758}},{{/}}"}}

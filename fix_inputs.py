import json
import base64
import sys
import subprocess
import urllib.parse
import re

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error running: {cmd}\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

repos = {
    "vish288/mcp-gitlab": {
        "inputs": [
            {
                "id": "gitlab-url",
                "type": "promptString",
                "description": "GitLab URL",
                "default": "https://gitlab.example.com"
            },
            {
                "id": "gitlab-token",
                "type": "promptString",
                "description": "GitLab Personal Access Token",
                "password": True
            }
        ]
    },
    "vish288/mcp-atlassian-extended": {
        "inputs": [
            {
                "id": "jira-url",
                "type": "promptString",
                "description": "Jira URL",
                "default": "https://your-company.atlassian.net"
            },
            {
                "id": "jira-username",
                "type": "promptString",
                "description": "Jira Username / Email"
            },
            {
                "id": "jira-api-token",
                "type": "promptString",
                "description": "Jira API Token",
                "password": True
            }
        ]
    }
}

for repo, config in repos.items():
    print(f"Updating {repo}...")
    
    file_info_json = run_cmd(f'gh api repos/{repo}/contents/README.md')
    file_info = json.loads(file_info_json)
    content = base64.b64decode(file_info["content"]).decode("utf-8")
    sha = file_info["sha"]
    
    inputs_json = json.dumps(config["inputs"], separators=(',', ':'))
    inputs_encoded = urllib.parse.quote(inputs_json)
    
    # We want to insert `&inputs=...` into the VS Code URL, before `&config=`
    def inject_inputs(match):
        url = match.group(1)
        # Remove old inputs if they exist
        url = re.sub(r'&inputs=[^&]+', '', url)
        # Remove logo/image params since they don't work and clutter the URL
        url = re.sub(r'&image=[^&]+', '', url)
        url = re.sub(r'&logo=[^&]+', '', url)
        url = re.sub(r'&icon=[^&]+', '', url)
        
        # Inject inputs before config
        url = url.replace('&config=', f'&inputs={inputs_encoded}&config=')
        return url
        
    new_content = re.sub(
        r'(https://insiders\.vscode\.dev/redirect/mcp/install\?[^)]+)',
        inject_inputs,
        content
    )
    
    # Commit changes
    new_content_b64 = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "docs: add inputs configuration to VS Code install button to prompt for credentials",
        "content": new_content_b64,
        "sha": sha,
        "branch": "main"
    }
    
    with open('payload.json', 'w') as f:
        json.dump(payload, f)
        
    # We will create a PR and merge it
    run_cmd(f"cd /tmp/{repo.split('/')[1]} && git pull origin main && git checkout -b fix/vscode-inputs && git push origin fix/vscode-inputs -f")
    run_cmd(f"gh api -X PUT repos/{repo}/contents/README.md --input payload.json -f branch=fix/vscode-inputs")
    run_cmd(f"cd /tmp/{repo.split('/')[1]} && gh pr create --head fix/vscode-inputs --base main --title 'docs: add inputs configuration to VS Code install button' --body 'Adds the missing inputs parameter to VS Code install URLs so it correctly prompts for tokens.'")
    run_cmd(f"cd /tmp/{repo.split('/')[1]} && gh pr merge --admin --squash --delete-branch")
    print(f"Successfully updated {repo} README.md!")

print("Done.")

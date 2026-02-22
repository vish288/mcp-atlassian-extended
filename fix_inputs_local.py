import re
import urllib.parse
import json

def process_file(filepath, inputs_config):
    with open(filepath, 'r') as f:
        content = f.read()
        
    inputs_json = json.dumps(inputs_config, separators=(',', ':'))
    inputs_encoded = urllib.parse.quote(inputs_json)
    
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
        r'(https://insiders\.vscode\.dev/redirect/mcp/install\?[^)\s]+)',
        inject_inputs,
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(new_content)

gitlab_inputs = [
    {
        "id": "gitlab-url",
        "type": "promptString",
        "description": "GitLab URL",
        "default": "https://gitlab.com"
    },
    {
        "id": "gitlab-token",
        "type": "promptString",
        "description": "GitLab Personal Access Token",
        "password": True
    }
]

atlassian_inputs = [
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

process_file('/tmp/mcp-gitlab/README.md', gitlab_inputs)
process_file('/tmp/mcp-atlassian-extended/README.md', atlassian_inputs)

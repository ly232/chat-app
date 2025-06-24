
'''An MCP server for demo purpose.

It keeps track of local git logs and diff against public repo.

Run with:

uv run --with-requirements  \
    /Users/${USER}/Desktop/github/chat-app/requirements.txt \
    /Users/${USER}/Desktop/github/chat-app/server/mcp/git_info.py
'''

from mcp.server.fastmcp import FastMCP
from typing import Dict

import subprocess

mcp = FastMCP('gitinfo')

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

@mcp.tool()
def get_git_info() -> Dict[str, str]:
    '''Returns git information from local git repo.
    
    Returns a dict keyed by git command, value is the output of the git command.
    '''
    print('!!!!! reaching inside get_git_info')
    return {
        'git remote -v': run_command('cd ~/Desktop/github/chat-app && git remote -v'),
        'git log --oneline': run_command('cd ~/Desktop/github/chat-app && git log --oneline'),
    }

@mcp.tool()
def get_host_info() -> str:
    '''get host information

    returns:
      str: the host information in json string.
    '''
    import platform
    info: dict[str, str] = {
        'system': platform.system(),
        'release': platform.release(),
    }
    return str(info)

if __name__ == '__main__':
    print('asdf1...')
    mcp.run(transport='stdio')

import os
import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient
from gitguard.clients.git_client import GitClient


@pytest.fixture(scope="session")
def gitea_base_url():
    return os.getenv("GITEA_BASE_URL", "http://gitea:3000")


@pytest.fixture(scope="session")
def gitea_host():
    return os.getenv("GITEA_HOST", "gitea:3000")

@pytest.fixture(scope="session")
def gitea_token():
    # CI will place token in mounted file or env
    token = os.getenv("GITEA_ADMIN_TOKEN", None)
    token_file = os.getenv("GITEA_ADMIN_TOKEN_FILE", "/data/gitea_admin_token")
    if not token and os.path.exists(token_file):
        with open(token_file, "r") as f:
            token = f.read().strip()
    return token

@pytest.fixture(scope="session")
def gitea_client(gitea_base_url, gitea_token) -> GiteaHttpClient:
    client = GiteaHttpClient(base_url=gitea_base_url, token=gitea_token)
    health = client.health_check()
    assert health.ok(), f"Gitea server not reachable at {gitea_base_url} (status={health.status_code})"
    return client

@pytest.fixture
def git_client(tmp_path) -> GitClient:
    # default git client with workdir per-test
    c = GitClient(workdir=str(tmp_path))
    return c

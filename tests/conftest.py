import os
import pytest
import base64
import logging
import subprocess

from gitguard.clients.http_gitea_client import GiteaHttpClient
from gitguard.clients.git_client import GitClient


logger = logging.getLogger("gitguard")


@pytest.fixture(scope="session")
def gitea_base_url():
    return os.getenv("GITEA_BASE_URL", "http://gitea:3000")


@pytest.fixture(scope="session")
def gitea_host():
    return os.getenv("GITEA_HOST", "gitea")


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
    version = client.version()
    assert version.ok(), f"Gitea server not reachable at {gitea_base_url} (status={version.status_code})"
    return client


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(gitea_client):
    """
    Prepare a reusable test environment for E2E:
      - ensure test user exists
      - ensure test repo exists (under that user)
      - ensure README.md file is present
    Runs once per CI session.
    """
    username = "testuser"
    email = "testuser@example.com"
    password = "Password123!"
    repo_name = "test-repo"

    # --- 1. Ensure test user exists ---
    logger.info("[setup] Ensuring test user '%s' exists", username)
    r = gitea_client.create_user(username=username, email=email, password=password)
    if not (r.ok() or r.status_code in (409, 422)):
        raise RuntimeError(f"Failed to create test user '{username}': {r.status_code} {r.text}")

    # --- 2. Ensure test repo exists ---
    logger.info("[setup] Ensuring test repo '%s/%s' exists", username, repo_name)
    r = gitea_client.admin_create_repo(username=username, repo_name=repo_name)
    if not (r.ok() or r.status_code == 409):
        raise RuntimeError(f"Failed to create repo '{repo_name}': {r.status_code} {r.text}")

    # --- 3. Ensure README.md exists ---
    # Try to fetch README.md using repo contents API
    r = gitea_client.get(f"repos/{username}/{repo_name}/contents/README.md", headers=gitea_client._auth_headers())
    if r.ok():
        logger.info("[setup] README.md already exists in '%s/%s'", username, repo_name)
        return

    # --- 4. Create README.md if missing ---
    logger.info("[setup] Creating README.md in '%s/%s'", username, repo_name)
    content = base64.b64encode(b"# Test Repository\n\nAuto-created for GitGuard E2E tests.\n").decode("utf-8")
    payload = {
        "content": content,
        "message": "Add initial README.md"
    }
    r = gitea_client.post(f"repos/{username}/{repo_name}/contents/README.md",
                          json=payload, headers=gitea_client._auth_headers())
    if not r.ok():
        raise RuntimeError(f"Failed to create README.md: {r.status_code} {r.text}")

    logger.info("[setup] Repo '%s/%s' ready for testing", username, repo_name)


# @pytest.fixture(scope="session", autouse=True)
# def cleanup_test_repo(gitea_client):
#     yield
#     username = "testuser"
#     repo_name = "test-repo"
#     logger.info("[cleanup] Deleting repo '%s/%s'", username, repo_name)
#     gitea_client.delete_repo(owner=username, repo=repo_name)


@pytest.fixture(scope="session", autouse=True)
def setup_git_identity():
    """Ensure git identity matches the test user created in setup_test_environment."""
    subprocess.run(["git", "config", "--global", "user.email", "testuser@example.com"], check=False)
    subprocess.run(["git", "config", "--global", "user.name", "testuser"], check=False)


@pytest.fixture
def git_client(tmp_path) -> GitClient:
    # default git client with workdir per-test
    c = GitClient(workdir=str(tmp_path))
    return c

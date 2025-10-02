import os
import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.fixture(scope="session")
def gitea_client() -> GiteaHttpClient:
    """
    Fixture for a Gitea HTTP client.
    Reads base_url and token from env (injected in docker-compose and CI).
    """
    base_url = os.getenv("GITEA_BASE_URL", "http://gitea:3000")
    token = os.getenv("GITEA_ADMIN_TOKEN", None)

    client = GiteaHttpClient(base_url=base_url, token=token)
    # quick smoke-check
    health = client.health_check()
    assert health.ok(), f"Gitea server not reachable at {base_url}, status={health.status_code}"

    return client

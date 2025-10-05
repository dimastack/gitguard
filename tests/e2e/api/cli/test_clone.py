import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_clone_public_repo(git_client, gitea_host, protocol, tmp_path):
    """
    Clone a known public repository from Gitea and verify local repo initialization.
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "test-org"
    git_client.repo = "test-repo"
    git_client.workdir = str(tmp_path)

    result = git_client.clone()
    assert result.ok(), f"Clone failed via {protocol}: {result.stderr}"

    git_dir = tmp_path / "test-repo" / ".git"
    assert git_dir.exists(), f".git directory missing for cloned repo via {protocol}"


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_clone_nonexistent_repo(git_client, gitea_host, protocol, tmp_path):
    """
    Attempt to clone a non-existent repo should fail cleanly.
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "test-org"
    git_client.repo = "no-such-repo-xyz"
    git_client.workdir = str(tmp_path)

    result = git_client.clone()
    assert not result.ok(), f"Expected clone failure via {protocol}, got success"
    assert "not found" in result.stderr.lower() or "fatal" in result.stderr.lower()

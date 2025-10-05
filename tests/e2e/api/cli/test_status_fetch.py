import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_status_clean_repo(git_client, gitea_host, tmp_path, protocol):
    """
    Check that freshly cloned repository has a clean working tree.
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(tmp_path)

    # Clone repo
    result = git_client.clone()
    assert result.ok(), f"Clone failed: {result.stderr}"

    repo_dir = tmp_path / "test-repo"
    git_client.workdir = str(repo_dir)

    # Check status
    status_result = git_client.status()
    assert status_result.ok(), f"Status command failed: {status_result.stderr}"
    assert (
        "nothing to commit" in status_result.stdout.lower()
        or "clean" in status_result.stdout.lower()
    ), f"Unexpected status output: {status_result.stdout}"


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_fetch_from_origin(git_client, gitea_host, tmp_path, protocol):
    """
    Fetch from origin should complete successfully.
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(tmp_path)

    # Clone repo
    result = git_client.clone()
    assert result.ok(), f"Clone failed: {result.stderr}"

    repo_dir = tmp_path / "test-repo"
    git_client.workdir = str(repo_dir)

    # Fetch
    fetch_result = git_client.fetch()
    assert fetch_result.ok(), f"Fetch failed: {fetch_result.stderr}"
    assert "fetch" in (
        fetch_result.stdout.lower() + fetch_result.stderr.lower()
    ), f"Unexpected fetch output: {fetch_result.stdout} {fetch_result.stderr}"

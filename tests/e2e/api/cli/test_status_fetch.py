import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_status_clean_repo(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    status_result = client2.status()
    assert status_result.ok()
    assert "nothing to commit" in status_result.stdout.lower() or "clean" in status_result.stdout.lower()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_fetch_from_origin(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    fetch_result = client2.fetch()
    assert fetch_result.ok()
    assert "fetch" in (fetch_result.stdout.lower() + fetch_result.stderr.lower())

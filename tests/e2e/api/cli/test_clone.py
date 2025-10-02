import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_clone_valid_repo(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    result = client.clone()
    assert result.ok()
    assert "cloning" in result.stdout.lower() or "checking out" in result.stdout.lower()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_clone_with_explicit_url(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    repo_url = client._make_repo_url()
    result = client.clone(repo_url=repo_url)
    assert result.ok()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_clone_invalid_repo(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="nonexistent", workdir=tmp_path)
    result = client.clone()
    assert not result.ok()
    assert "fatal" in result.stderr.lower()

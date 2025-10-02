import pytest

from clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_create_and_switch_branch(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    branch_result = client2.branch("feature/test-branch")
    assert branch_result.ok()

    checkout_result = client2.checkout("feature/test-branch")
    assert checkout_result.ok()

    back_result = client2.checkout("main")
    assert back_result.ok()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_checkout_nonexistent_branch(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    switch_result = client2.checkout("no-such-branch")
    assert not switch_result.ok()

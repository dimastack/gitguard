import pytest

from clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_push_and_pull_roundtrip(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    (repo_dir / "hello.txt").write_text("hello world")
    client2.add("hello.txt")
    client2.commit("add hello.txt")

    push_result = client2.push()
    assert push_result.ok()

    pull_result = client2.pull()
    assert pull_result.ok()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_pull_on_clean_repo(protocol, tmp_path):
    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=tmp_path)
    client.clone()

    repo_dir = tmp_path / "test-repo"
    client2 = GitClient(protocol=protocol, host="localhost:3000",
                        owner="testuser", repo="test-repo", workdir=repo_dir)

    pull_result = client2.pull()
    assert pull_result.ok()
    assert "up to date" in pull_result.stdout.lower() or "already up to date" in pull_result.stdout.lower()

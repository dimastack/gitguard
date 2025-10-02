import pytest
from clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_init_and_commit(protocol, tmp_path):
    repo_dir = tmp_path / "local"
    repo_dir.mkdir()

    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=repo_dir)

    # init
    init_result = client.init()
    assert init_result.ok()

    # create file
    f = repo_dir / "a.txt"
    f.write_text("line1")

    add_result = client.add("a.txt")
    assert add_result.ok()

    commit_result = client.commit("initial commit")
    assert commit_result.ok()


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_commit_without_add(protocol, tmp_path):
    repo_dir = tmp_path / "local"
    repo_dir.mkdir()

    client = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=repo_dir)

    client.init()
    (repo_dir / "b.txt").write_text("line2")

    commit_result = client.commit("try commit without add")
    assert not commit_result.ok()
    assert "nothing to commit" in (commit_result.stdout + commit_result.stderr).lower()

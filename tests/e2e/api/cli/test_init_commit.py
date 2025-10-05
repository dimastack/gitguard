import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_init_and_commit(git_client, gitea_host, protocol, tmp_path):
    repo_dir = tmp_path / "local"
    repo_dir.mkdir()

    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(repo_dir)

    # init
    init_result = git_client.init()
    assert init_result.ok(), f"Init failed: {init_result.stderr}"

    # create file
    f = repo_dir / "a.txt"
    f.write_text("line1")

    add_result = git_client.add("a.txt")
    assert add_result.ok(), f"Add failed: {add_result.stderr}"

    commit_result = git_client.commit("initial commit")
    assert commit_result.ok(), f"Commit failed: {commit_result.stderr}"


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_commit_without_add(git_client, gitea_host, protocol, tmp_path):
    repo_dir = tmp_path / "local"
    repo_dir.mkdir()

    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(repo_dir)

    git_client.init()
    (repo_dir / "b.txt").write_text("line2")

    commit_result = git_client.commit("try commit without add")
    assert not commit_result.ok(), "Expected commit to fail without add"
    combined_output = (commit_result.stdout + commit_result.stderr).lower()
    assert "nothing to commit" in combined_output or "no changes added" in combined_output, \
        f"Unexpected commit output: {combined_output}"

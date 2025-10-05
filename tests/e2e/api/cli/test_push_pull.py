import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_push_and_pull_roundtrip(git_client, gitea_host, tmp_path, protocol):
    """
    Scenario:
    1. Clone remote repo
    2. Add and commit new file
    3. Push changes
    4. Pull changes back
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)
    git_client.clone()

    repo_dir = tmp_path / "test-repo"
    git_client.workdir = str(repo_dir)

    (repo_dir / "hello.txt").write_text("hello world")
    assert git_client.add("hello.txt").ok()
    assert git_client.commit("add hello.txt").ok()

    push_result = git_client.push()
    assert push_result.ok(), f"Push failed: {push_result.stderr}"

    pull_result = git_client.pull()
    assert pull_result.ok(), f"Pull failed: {pull_result.stderr}"


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_pull_on_clean_repo(git_client, gitea_host, tmp_path, protocol):
    """
    Scenario:
    1. Clone clean repo
    2. Pull from remote (should be up to date)
    """
    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)
    git_client.clone()

    repo_dir = tmp_path / "test-repo"
    git_client.workdir = str(repo_dir)

    pull_result = git_client.pull()
    assert pull_result.ok(), f"Pull failed: {pull_result.stderr}"
    assert (
        "up to date" in pull_result.stdout.lower()
        or "already up to date" in pull_result.stdout.lower()
    ), f"Unexpected pull output: {pull_result.stdout}"

import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_full_git_flow(git_client, gitea_host, protocol, tmp_path):
    """
    Full lifecycle:
    1. init local repo
    2. add + commit
    3. branch + checkout
    4. clone into another copy
    5. push/pull between copies
    6. fetch + status
    + validation of file contents
    """

    # -------------------------
    # Local init & first commit
    # -------------------------
    repo_dir = tmp_path / "local"
    repo_dir.mkdir()

    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(repo_dir)

    init_result = git_client.init()
    assert init_result.ok(), f"Init failed: {init_result.stderr}"

    f1 = repo_dir / "file1.txt"
    f1.write_text("first line")

    add_result = git_client.add("file1.txt")
    assert add_result.ok(), f"Add failed: {add_result.stderr}"

    commit_result = git_client.commit("initial commit")
    assert commit_result.ok(), f"Commit failed: {commit_result.stderr}"

    # ---------
    # Branching
    # ---------
    branch_result = git_client.branch("feature/one")
    assert branch_result.ok(), f"Branch creation failed: {branch_result.stderr}"

    checkout_result = git_client.checkout("feature/one")
    assert checkout_result.ok(), f"Checkout failed: {checkout_result.stderr}"

    # back to main
    back_result = git_client.checkout("main")
    assert back_result.ok(), f"Checkout main failed: {back_result.stderr}"

    # -----------------
    # Clone remote copy
    # -----------------
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()

    cloner = git_client.__class__(
        protocol=protocol,
        host=gitea_host,
        owner="testuser",
        repo="test-repo",
        workdir=str(clone_dir)
    )

    clone_result = cloner.clone()
    assert clone_result.ok(), f"Clone failed: {clone_result.stderr}"

    repo_cloned_dir = clone_dir / "test-repo"
    clone2 = git_client.__class__(
        protocol=protocol,
        host=gitea_host,
        owner="testuser",
        repo="test-repo",
        workdir=str(repo_cloned_dir)
    )

    # file from the first commit should already be there
    f1_cloned = repo_cloned_dir / "file1.txt"
    assert f1_cloned.exists(), "File1 missing in clone"
    assert f1_cloned.read_text() == "first line"

    # ----------------
    # Push/pull roundtrip
    # ----------------
    f2 = repo_dir / "file2.txt"
    f2.write_text("second line")
    git_client.add("file2.txt")
    git_client.commit("add file2.txt")

    push_result = git_client.push()
    assert push_result.ok(), f"Push failed: {push_result.stderr}"

    pull_result = clone2.pull()
    assert pull_result.ok(), f"Pull failed: {pull_result.stderr}"

    # after pull file2 should appear in the cloned repo
    f2_cloned = repo_cloned_dir / "file2.txt"
    assert f2_cloned.exists(), "file2.txt missing in cloned repo"
    assert f2_cloned.read_text() == "second line"

    # ----------------
    # Fetch + Status
    # ----------------
    fetch_result = clone2.fetch()
    assert fetch_result.ok(), f"Fetch failed: {fetch_result.stderr}"

    status_result = clone2.status()
    assert status_result.ok(), f"Status failed: {status_result.stderr}"
    assert (
        "clean" in status_result.stdout.lower()
        or "nothing to commit" in status_result.stdout.lower()
    ), f"Unexpected status output: {status_result.stdout}"

import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_full_git_flow(protocol, tmp_path):
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

    local = GitClient(protocol=protocol, host="localhost:3000",
                      owner="testuser", repo="test-repo", workdir=repo_dir)

    init_result = local.init()
    assert init_result.ok()

    f1 = repo_dir / "file1.txt"
    f1.write_text("first line")

    add_result = local.add("file1.txt")
    assert add_result.ok()

    commit_result = local.commit("initial commit")
    assert commit_result.ok()

    # ---------
    # Branching
    # ---------
    branch_result = local.branch("feature/one")
    assert branch_result.ok()

    checkout_result = local.checkout("feature/one")
    assert checkout_result.ok()

    # back to main
    back_result = local.checkout("main")
    assert back_result.ok()

    # -----------------
    # Clone remote copy
    # -----------------
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()

    cloner = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=clone_dir)

    clone_result = cloner.clone()
    assert clone_result.ok()

    repo_cloned_dir = clone_dir / "test-repo"
    clone2 = GitClient(protocol=protocol, host="localhost:3000",
                       owner="testuser", repo="test-repo", workdir=repo_cloned_dir)

    # file from the first commit should already be there
    f1_cloned = repo_cloned_dir / "file1.txt"
    assert f1_cloned.exists()
    assert f1_cloned.read_text() == "first line"

    # ----------------
    # Push/pull roundtrip
    # ----------------
    f2 = repo_dir / "file2.txt"
    f2.write_text("second line")
    local.add("file2.txt")
    local.commit("add file2.txt")

    push_result = local.push()
    assert push_result.ok()

    pull_result = clone2.pull()
    assert pull_result.ok()

    # after pull file2 should appear in the cloned repo
    f2_cloned = repo_cloned_dir / "file2.txt"
    assert f2_cloned.exists()
    assert f2_cloned.read_text() == "second line"

    # ----------------
    # Fetch + Status
    # ----------------
    fetch_result = clone2.fetch()
    assert fetch_result.ok()

    status_result = clone2.status()
    assert status_result.ok()
    assert "clean" in status_result.stdout.lower() or "nothing to commit" in status_result.stdout.lower()

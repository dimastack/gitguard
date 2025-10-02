import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_git_log_diff_reset_stash(tmp_path, protocol):
    """
    Scenario:
    1. init repo
    2. create file, commit
    3. create new commit
    4. check log has 2 commits
    5. diff between commits
    6. reset to first commit
    7. stash uncommitted changes
    8. apply stash
    9. drop stash
    """

    workdir = tmp_path / "repo"
    workdir.mkdir()

    client = GitClient(protocol=protocol, host="gitea", owner="bob", repo="hist-demo", workdir=str(workdir))

    # 1. init repo
    result = client.init()
    assert result.ok(), f"Init failed: {result.stderr}"

    # 2. create first file + commit
    f1 = workdir / "a.txt"
    f1.write_text("first line\n")
    result = client.add("a.txt")
    assert result.ok(), f"Add failed: {result.stderr}"
    result = client.commit("initial commit")
    assert result.ok(), f"Commit1 failed: {result.stderr}"

    # 3. modify file + commit again
    f1.write_text("first line\nsecond line\n")
    result = client.add("a.txt")
    assert result.ok(), f"Add 2 failed: {result.stderr}"
    result = client.commit("second commit")
    assert result.ok(), f"Commit2 failed: {result.stderr}"

    # 4. check log has 2 commits
    result = client._run(["log", "--oneline"])
    assert result.ok(), f"Log failed: {result.stderr}"
    log_lines = result.stdout.strip().splitlines()
    assert len(log_lines) == 2, f"Expected 2 commits, got: {log_lines}"

    # 5. diff between commits
    result = client._run(["diff", "HEAD~1", "HEAD"])
    assert result.ok(), f"Diff failed: {result.stderr}"
    assert "+second line" in result.stdout, "Expected diff showing added line"

    # 6. reset to first commit
    result = client._run(["reset", "--hard", "HEAD~1"])
    assert result.ok(), f"Reset failed: {result.stderr}"
    assert f1.read_text() == "first line\n", "File content not reset after hard reset"

    # 7. stash uncommitted changes
    f1.write_text("modified but not committed\n")
    result = client._run(["stash"])
    assert result.ok(), f"Stash failed: {result.stderr}"

    # verify stash list has 1 entry
    result = client._run(["stash", "list"])
    assert result.ok(), f"Stash list failed: {result.stderr}"
    stash_entries = result.stdout.strip().splitlines()
    assert len(stash_entries) == 1, f"Expected 1 stash, got: {stash_entries}"

    # 8. apply stash
    result = client._run(["stash", "apply"])
    assert result.ok(), f"Stash apply failed: {result.stderr}"
    assert "modified but not committed" in f1.read_text(), "Stash apply did not restore changes"

    # 9. drop stash
    result = client._run(["stash", "drop"])
    assert result.ok(), f"Stash drop failed: {result.stderr}"

    # verify stash list is empty
    result = client._run(["stash", "list"])
    assert result.ok(), f"Stash list after drop failed: {result.stderr}"
    assert result.stdout.strip() == "", f"Expected no stash entries, got: {result.stdout}"

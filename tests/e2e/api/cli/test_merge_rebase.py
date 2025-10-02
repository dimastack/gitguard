import os
import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
def test_merge_branch_success(tmp_path):
    """
    Scenario:
    - Init repo
    - Create 'feature' branch and commit
    - Merge back into main
    - Verify merged content
    """
    client = GitClient(workdir=tmp_path)
    assert client.init().ok()

    (tmp_path / "file_main.txt").write_text("main branch content")
    assert client.add("file_main.txt").ok()
    assert client.commit("main commit").ok()

    assert client.branch("feature").ok()
    assert client.checkout("feature").ok()

    (tmp_path / "file_feature.txt").write_text("feature branch content")
    assert client.add("file_feature.txt").ok()
    assert client.commit("feature commit").ok()

    assert client.checkout("main").ok()
    merge_result = client.merge("feature")
    assert merge_result.ok(), f"Merge failed: {merge_result.stderr}"

    files = os.listdir(tmp_path)
    assert "file_main.txt" in files
    assert "file_feature.txt" in files

    log = client.log("--oneline").stdout
    assert "main commit" in log
    assert "feature commit" in log


@pytest.mark.e2e
def test_rebase_success(tmp_path):
    """
    Scenario:
    - Init repo
    - Commit in main
    - Commit in feature
    - Commit again in main
    - Rebase feature onto main
    """
    client = GitClient(workdir=tmp_path)
    assert client.init().ok()

    (tmp_path / "a.txt").write_text("a1")
    assert client.add("a.txt").ok()
    assert client.commit("main-1").ok()

    assert client.branch("feature").ok()
    assert client.checkout("feature").ok()

    (tmp_path / "b.txt").write_text("b1")
    assert client.add("b.txt").ok()
    assert client.commit("feature-1").ok()

    assert client.checkout("main").ok()
    (tmp_path / "a.txt").write_text("a2")
    assert client.add("a.txt").ok()
    assert client.commit("main-2").ok()

    assert client.checkout("feature").ok()
    rebase_result = client.rebase("main")
    assert rebase_result.ok(), f"Rebase failed: {rebase_result.stderr}"

    log = client.log("--oneline").stdout
    assert "feature-1" in log
    assert "main-2" in log


@pytest.mark.e2e
def test_rebase_conflict(tmp_path):
    """
    Scenario:
    - Init repo
    - Branch 'feature'
    - Modify same file in both branches
    - Rebase → expect conflict
    """
    client = GitClient(workdir=tmp_path)
    assert client.init().ok()

    (tmp_path / "conflict.txt").write_text("base")
    assert client.add("conflict.txt").ok()
    assert client.commit("base commit").ok()

    assert client.branch("feature").ok()

    (tmp_path / "conflict.txt").write_text("main change")
    assert client.add("conflict.txt").ok()
    assert client.commit("main change").ok()

    assert client.checkout("feature").ok()
    (tmp_path / "conflict.txt").write_text("feature change")
    assert client.add("conflict.txt").ok()
    assert client.commit("feature change").ok()

    result = client.rebase("main")
    assert not result.ok()
    assert "CONFLICT" in result.stderr or "error" in result.stderr.lower()


@pytest.mark.e2e
def test_fast_forward_merge(tmp_path):
    """
    Scenario:
    - Init repo
    - Feature branch with commit
    - Merge back (fast-forward)
    """
    client = GitClient(workdir=tmp_path)
    assert client.init().ok()

    # Initial empty commit (main branch baseline)
    assert client.commit("initial", allow_empty=True).ok()

    assert client.branch("feature").ok()
    assert client.checkout("feature").ok()

    (tmp_path / "f.txt").write_text("feature")
    assert client.add("f.txt").ok()
    assert client.commit("feature commit").ok()

    assert client.checkout("main").ok()
    merge_result = client.merge("feature")
    assert merge_result.ok(), f"Merge failed: {merge_result.stderr}"

    log = client.log("--oneline").stdout
    assert "feature commit" in log

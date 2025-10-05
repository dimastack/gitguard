import os
import pytest


@pytest.mark.e2e
def test_merge_branch_success(git_client, gitea_host, tmp_path):
    """
    Scenario:
    - Init repo
    - Create 'feature' branch and commit
    - Merge back into main
    - Verify merged content
    """
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)

    assert git_client.init().ok()

    (tmp_path / "file_main.txt").write_text("main branch content")
    assert git_client.add("file_main.txt").ok()
    assert git_client.commit("main commit").ok()

    assert git_client.branch("feature").ok()
    assert git_client.checkout("feature").ok()

    (tmp_path / "file_feature.txt").write_text("feature branch content")
    assert git_client.add("file_feature.txt").ok()
    assert git_client.commit("feature commit").ok()

    assert git_client.checkout("main").ok()
    merge_result = git_client.merge("feature")
    assert merge_result.ok(), f"Merge failed: {merge_result.stderr}"

    files = os.listdir(tmp_path)
    assert "file_main.txt" in files
    assert "file_feature.txt" in files

    log = git_client.log("--oneline").stdout
    assert "main commit" in log
    assert "feature commit" in log


@pytest.mark.e2e
def test_rebase_success(git_client, gitea_host, tmp_path):
    """
    Scenario:
    - Init repo
    - Commit in main
    - Commit in feature
    - Commit again in main
    - Rebase feature onto main
    """
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)

    assert git_client.init().ok()

    (tmp_path / "a.txt").write_text("a1")
    assert git_client.add("a.txt").ok()
    assert git_client.commit("main-1").ok()

    assert git_client.branch("feature").ok()
    assert git_client.checkout("feature").ok()

    (tmp_path / "b.txt").write_text("b1")
    assert git_client.add("b.txt").ok()
    assert git_client.commit("feature-1").ok()

    assert git_client.checkout("main").ok()
    (tmp_path / "a.txt").write_text("a2")
    assert git_client.add("a.txt").ok()
    assert git_client.commit("main-2").ok()

    assert git_client.checkout("feature").ok()
    rebase_result = git_client.rebase("main")
    assert rebase_result.ok(), f"Rebase failed: {rebase_result.stderr}"

    log = git_client.log("--oneline").stdout
    assert "feature-1" in log
    assert "main-2" in log


@pytest.mark.e2e
def test_rebase_conflict(git_client, gitea_host, tmp_path):
    """
    Scenario:
    - Init repo
    - Branch 'feature'
    - Modify same file in both branches
    - Rebase → expect conflict
    """
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)

    assert git_client.init().ok()

    (tmp_path / "conflict.txt").write_text("base")
    assert git_client.add("conflict.txt").ok()
    assert git_client.commit("base commit").ok()

    assert git_client.branch("feature").ok()

    (tmp_path / "conflict.txt").write_text("main change")
    assert git_client.add("conflict.txt").ok()
    assert git_client.commit("main change").ok()

    assert git_client.checkout("feature").ok()
    (tmp_path / "conflict.txt").write_text("feature change")
    assert git_client.add("conflict.txt").ok()
    assert git_client.commit("feature change").ok()

    result = git_client.rebase("main")
    assert not result.ok()
    assert "CONFLICT" in result.stderr or "error" in result.stderr.lower()


@pytest.mark.e2e
def test_fast_forward_merge(git_client, gitea_host, tmp_path):
    """
    Scenario:
    - Init repo
    - Feature branch with commit
    - Merge back (fast-forward)
    """
    git_client.host = gitea_host
    git_client.workdir = str(tmp_path)

    assert git_client.init().ok()

    # Initial empty commit (main branch baseline)
    assert git_client.commit("initial", allow_empty=True).ok()

    assert git_client.branch("feature").ok()
    assert git_client.checkout("feature").ok()

    (tmp_path / "f.txt").write_text("feature")
    assert git_client.add("f.txt").ok()
    assert git_client.commit("feature commit").ok()

    assert git_client.checkout("main").ok()
    merge_result = git_client.merge("feature")
    assert merge_result.ok(), f"Merge failed: {merge_result.stderr}"

    log = git_client.log("--oneline").stdout
    assert "feature commit" in log

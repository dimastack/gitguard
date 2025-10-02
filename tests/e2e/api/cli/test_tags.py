import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_git_tags(tmp_path, protocol):
    """
    Scenario:
    1. init repo
    2. create commit
    3. create tag
    4. verify tag exists
    5. create second commit + tag
    6. list tags -> 2
    7. delete one tag
    8. negative: try to checkout non-existing tag
    """

    workdir = tmp_path / "repo"
    workdir.mkdir()

    client = GitClient(protocol=protocol, host="gitea", owner="bob", repo="tag-demo", workdir=str(workdir))

    # 1. init repo
    result = client.init()
    assert result.ok(), f"Init failed: {result.stderr}"

    # 2. create file + commit
    f1 = workdir / "main.txt"
    f1.write_text("v1 content\n")
    result = client.add("main.txt")
    assert result.ok(), f"Add failed: {result.stderr}"
    result = client.commit("first commit")
    assert result.ok(), f"Commit1 failed: {result.stderr}"

    # 3. create tag v1.0
    result = client._run(["tag", "v1.0"])
    assert result.ok(), f"Tag creation failed: {result.stderr}"

    # 4. verify tag exists
    result = client._run(["tag"])
    assert result.ok(), f"Tag list failed: {result.stderr}"
    tags = result.stdout.strip().splitlines()
    assert "v1.0" in tags, f"Expected tag 'v1.0' in {tags}"

    # 5. new commit + tag v2.0
    f1.write_text("v2 content\n")
    result = client.add("main.txt")
    assert result.ok(), f"Add2 failed: {result.stderr}"
    result = client.commit("second commit")
    assert result.ok(), f"Commit2 failed: {result.stderr}"
    result = client._run(["tag", "v2.0"])
    assert result.ok(), f"Tag v2.0 creation failed: {result.stderr}"

    # 6. list tags -> expect 2
    result = client._run(["tag"])
    assert result.ok(), f"Tag list 2 failed: {result.stderr}"
    tags = result.stdout.strip().splitlines()
    assert set(tags) == {"v1.0", "v2.0"}, f"Expected tags ['v1.0','v2.0'], got {tags}"

    # 7. delete tag v1.0
    result = client._run(["tag", "-d", "v1.0"])
    assert result.ok(), f"Tag delete failed: {result.stderr}"
    result = client._run(["tag"])
    assert result.ok(), f"Tag list after delete failed: {result.stderr}"
    tags = result.stdout.strip().splitlines()
    assert "v1.0" not in tags, f"Tag 'v1.0' should be deleted, got {tags}"
    assert "v2.0" in tags, f"Tag 'v2.0' missing after delete step"

    # 8. negative: checkout non-existing tag
    result = client._run(["checkout", "v3.0"])
    assert not result.ok(), "Checkout of non-existing tag v3.0 should fail"
    assert "did not match any file(s)" in (result.stderr or result.stdout), f"Unexpected error msg: {result.stderr or result.stdout}"

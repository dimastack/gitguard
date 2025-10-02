import pytest

from clients.git_client import GitClient


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_git_remote_configuration(tmp_path, protocol):
    """
    Scenario:
    1. init repo
    2. add remote
    3. verify remote
    4. change remote URL
    5. remove remote
    6. negative: fetch from removed remote
    """

    workdir = tmp_path / "repo"
    workdir.mkdir()

    client = GitClient(protocol=protocol, host="gitea", owner="alice", repo="remote-demo", workdir=str(workdir))

    # 1. init repo
    result = client.init()
    assert result.ok(), f"Init failed: {result.stderr}"

    # 2. add remote
    result = client._run(["remote", "add", "origin", client.repo_url])
    assert result.ok(), f"Remote add failed: {result.stderr}"

    # 3. verify remote
    result = client._run(["remote", "-v"])
    assert result.ok(), f"Remote -v failed: {result.stderr}"
    remotes = result.stdout.splitlines()
    assert any("origin" in r and client.repo_url in r for r in remotes), \
        f"Origin not found in remotes: {remotes}"

    # 4. change remote URL
    new_url = client.repo_url.replace(client.repo, f"{client.repo}-alt")
    result = client._run(["remote", "set-url", "origin", new_url])
    assert result.ok(), f"Set-url failed: {result.stderr}"

    # verify updated remote
    result = client._run(["remote", "-v"])
    assert result.ok(), f"Remote -v after update failed: {result.stderr}"
    remotes = result.stdout.splitlines()
    assert any("origin" in r and new_url in r for r in remotes), \
        f"Updated remote not found: {remotes}"

    # 5. remove remote
    result = client._run(["remote", "remove", "origin"])
    assert result.ok(), f"Remove remote failed: {result.stderr}"

    # verify removal
    result = client._run(["remote", "-v"])
    assert result.ok(), f"Remote -v after remove failed: {result.stderr}"
    assert result.stdout.strip() == "", f"Expected no remotes, got: {result.stdout}"

    # 6. negative: fetch from removed remote
    result = client._run(["fetch", "origin"])
    assert not result.ok(), "Fetch from removed remote unexpectedly succeeded"
    assert "No such remote" in result.stderr or "not found" in result.stderr.lower()

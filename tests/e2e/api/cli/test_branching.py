import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_create_and_switch_branch(git_client, gitea_host, protocol, tmp_path):
    """
    E2E: clone repo, create new branch, switch to it and back to main.
    """

    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(tmp_path)

    # 1. Clone repository
    clone_result = git_client.clone()
    assert clone_result.ok(), f"Clone failed: {clone_result.stderr}"

    # 2. Work in cloned repo
    repo_dir = tmp_path / "test-repo"
    branch_client = type(git_client)(
        protocol=protocol,
        host=gitea_host,
        owner="testuser",
        repo="test-repo",
        workdir=str(repo_dir),
    )

    # 3. Create new branch
    branch_result = branch_client.branch("feature/test-branch")
    assert branch_result.ok(), f"Branch creation failed: {branch_result.stderr}"

    # 4. Checkout new branch
    checkout_result = branch_client.checkout("feature/test-branch")
    assert checkout_result.ok(), f"Checkout failed: {checkout_result.stderr}"

    # 5. Switch back to main
    back_result = branch_client.checkout("main")
    assert back_result.ok(), f"Switch back to main failed: {back_result.stderr}"


@pytest.mark.e2e
@pytest.mark.parametrize("protocol", ["http", "ssh", "git"])
def test_checkout_nonexistent_branch(git_client, gitea_host, protocol, tmp_path):
    """
    E2E: attempting to checkout a non-existent branch should fail.
    """

    git_client.protocol = protocol
    git_client.host = gitea_host
    git_client.owner = "testuser"
    git_client.repo = "test-repo"
    git_client.workdir = str(tmp_path)

    # 1. Clone
    clone_result = git_client.clone()
    assert clone_result.ok(), f"Clone failed: {clone_result.stderr}"

    # 2. Attempt checkout to non-existent branch
    repo_dir = tmp_path / "test-repo"
    branch_client = type(git_client)(
        protocol=protocol,
        host=gitea_host,
        owner="testuser",
        repo="test-repo",
        workdir=str(repo_dir),
    )

    switch_result = branch_client.checkout("no-such-branch")

    # 3. Validate failure
    assert not switch_result.ok(), "Expected checkout to fail for non-existent branch"
    stderr = (switch_result.stderr or "").lower()
    assert "did not match any" in stderr or "unknown revision" in stderr or switch_result.returncode != 0, \
        f"Unexpected checkout result: {switch_result.returncode}, stderr={switch_result.stderr}"

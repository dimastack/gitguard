import pytest


@pytest.mark.e2e
def test_health_and_version(gitea_client):
    """
    Basic health/version checks of Gitea API.
    """

    # Health check should pass
    res = gitea_client.health_check()
    assert res.ok(), f"Health-check failed: {res.status_code} {getattr(res, 'text', '')}"

    # Version endpoint should return JSON with version info
    res = gitea_client.version()
    assert res.ok(), f"Version endpoint failed: {res.status_code} {getattr(res, 'text', '')}"
    data = res.json()
    assert isinstance(data, dict), f"Version response must be JSON object, got: {type(data)}"
    assert any(k in data for k in ("version", "tag_name", "sha", "version_tag")), \
        f"Unexpected version payload: {data}"


@pytest.mark.e2e
def test_repo_rename_and_delete(gitea_client):
    """
    Create a repo for a test user, rename it, verify rename, then delete and verify deletion.
    """

    username = "misc_repo_owner"
    email = "misc_repo_owner@example.com"
    password = "Password123!"
    original_repo = "misc-repo"
    renamed_repo = "misc-repo-renamed"

    # Ensure owner exists
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code in (422, 409), \
        f"Precondition: create_user failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # Create repo under the user
    resp = gitea_client.create_repo(original_repo, private=False, description="misc repo")
    assert resp.ok(), f"Repo creation failed: {resp.status_code} {getattr(resp, 'text', '')}"
    repo_data = resp.json()
    assert repo_data.get("name") == original_repo or repo_data.get("full_name", "").endswith(original_repo), \
        f"Unexpected repo data after create: {repo_data}"

    # Rename repository
    resp = gitea_client.rename_repo(owner=username, repo=original_repo, new_name=renamed_repo)
    assert resp.ok(), f"Rename repo failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # Verify old repo no longer exists
    r_old = gitea_client.get_repo(owner=username, repo=original_repo)
    assert not r_old.ok(), f"Old repo name still exists after rename: {r_old.status_code}"

    # Verify new repo exists
    r_new = gitea_client.get_repo(owner=username, repo=renamed_repo)
    assert r_new.ok(), f"Renamed repo not found: {r_new.status_code} {getattr(r_new, 'text', '')}"
    data = r_new.json()
    assert data.get("name") == renamed_repo or data.get("full_name", "").endswith(renamed_repo)

    # Delete repo
    resp = gitea_client.delete_repo(owner=username, repo=renamed_repo)
    assert resp.ok(), f"Delete repo failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # Verify deletion
    resp = gitea_client.get_repo(owner=username, repo=renamed_repo)
    assert not resp.ok(), f"Repository still present after delete: {resp.status_code}"
    assert resp.status_code == 404, f"Expected 404 after delete, got {resp.status_code} {getattr(resp, 'text', '')}"


@pytest.mark.e2e
def test_list_unadopted_and_adopt_negative(gitea_client):
    """
    Check admin unadopted repos endpoint and negative adoption case.
    """

    # List unadopted repos (should succeed)
    resp = gitea_client.list_unadopted_repos()
    assert resp.ok(), f"List unadopted repos failed: {resp.status_code} {getattr(resp, 'text', '')}"
    data = resp.json()
    assert isinstance(data, list), f"Unadopted repos endpoint must return list, got {type(data)}"

    # Negative: adopt non-existing repo -> expect 4xx failure
    fake_owner = "noone"
    fake_repo = "no-such-repo-xyz"
    resp = gitea_client.adopt_unadopted_repo(owner=fake_owner, repo_name=fake_repo)
    assert not resp.ok(), "Adopting non-existent repo unexpectedly succeeded"
    assert resp.status_code in (400, 404, 422), \
        f"Unexpected status for adopt failure: {resp.status_code} {getattr(resp, 'text', '')}"


@pytest.mark.e2e
def test_create_repo_invalid_payload(gitea_client):
    """
    Negative: creating a repository with invalid body (empty name) must fail.
    """

    username = "invalid_payload_user"
    email = "invalid_payload@example.com"
    password = "Password123!"

    # Prepare user
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code in (422, 409)

    # Try invalid repo create
    resp = gitea_client.create_repo(name="", private=False, description="should fail")
    assert not resp.ok(), "Creating repo with empty name should fail"
    assert resp.status_code in (400, 422), \
        f"Expected validation error, got {resp.status_code} {getattr(resp, 'text', '')}"

import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.mark.e2e
def test_health_and_version(gitea_client: GiteaHttpClient):
    """
    Basic health/version checks of Gitea API.
    """
    # health_check should be reachable
    res = gitea_client.health_check()
    assert res.ok(), f"Health-check failed: {res.status} {getattr(res, 'text', '')}"

    # version endpoint should return JSON with some version info
    res = gitea_client.version()
    assert res.ok(), f"Version endpoint failed: {res.status} {getattr(res, 'text', '')}"
    data = res.json()
    assert isinstance(data, dict), f"Version response must be JSON object, got: {type(data)}"
    # at minimum expect some key describing version info
    assert any(k in data for k in ("version", "tag_name", "sha", "version_tag")), f"Unexpected version payload: {data}"


@pytest.mark.e2e
def test_repo_rename_and_delete(gitea_client: GiteaHttpClient):
    """
    Create a repo for a test user, rename it, verify rename, then delete and verify deletion.
    """
    username = "misc_repo_owner"
    email = "misc_repo_owner@example.com"
    password = "Password123!"
    original_repo = "misc-repo"
    renamed_repo = "misc-repo-renamed"

    # ensure owner exists (create_user may return 422 if already exists)
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status in (422, 409), f"Precondition: create_user failed: {r.status} {getattr(r,'text','')}"

    # create repo under the user
    r = gitea_client.create_repo(original_repo, private=False, description="misc repo")
    assert r.ok(), f"Repo creation failed: {r.status} {getattr(r,'text','')}"
    repo_data = r.json()
    assert repo_data.get("name") == original_repo or repo_data.get("full_name", "").endswith(original_repo), \
        f"Unexpected repo data after create: {repo_data}"

    # rename repository (patch)
    r = gitea_client.rename_repo(owner=username, repo=original_repo, new_name=renamed_repo)
    assert r.ok(), f"Rename repo failed: {r.status} {getattr(r,'text','')}"
    # after rename, fetching old name should fail
    r_old = gitea_client.get_repo(owner=username, repo=original_repo)
    assert not r_old.ok(), f"Old repo name still exists after rename: {r_old.status}"
    # fetching new name should succeed
    r_new = gitea_client.get_repo(owner=username, repo=renamed_repo)
    assert r_new.ok(), f"Renamed repo not found: {r_new.status} {getattr(r_new,'text','')}"
    assert r_new.json().get("name") == renamed_repo or r_new.json().get("full_name","").endswith(renamed_repo)

    # delete repo
    r = gitea_client.delete_repo(owner=username, repo=renamed_repo)
    assert r.ok(), f"Delete repo failed: {r.status} {getattr(r,'text','')}"

    # verify deletion
    r = gitea_client.get_repo(owner=username, repo=renamed_repo)
    assert not r.ok(), f"Repository still present after delete: {r.status}"
    assert r.status == 404, f"Expected 404 after delete, got {r.status} {getattr(r,'text','')}"


@pytest.mark.e2e
def test_list_unadopted_and_adopt_negative(gitea_client: GiteaHttpClient):
    """
    Check admin unadopted repos endpoint and negative adoption case.
    """
    # list unadopted repos (should succeed and return a list)
    r = gitea_client.list_unadopted_repos()
    assert r.ok(), f"List unadopted repos failed: {r.status} {getattr(r,'text','')}"
    data = r.json()
    assert isinstance(data, list), f"Unadopted repos endpoint must return list, got {type(data)}"

    # negative: try to adopt a repo that likely doesn't exist -> expect failure
    fake_owner = "noone"
    fake_repo = "no-such-repo-xyz"
    r = gitea_client.adopt_unadopted_repo(owner=fake_owner, repo_name=fake_repo)
    # adoption of non-existing/unadopted repo should fail (either 4xx or specific error)
    assert not r.ok(), "Adopting non-existent repo unexpectedly succeeded"
    assert r.status in (400, 404, 422), f"Unexpected status for adopt failure: {r.status} {getattr(r,'text','')}"


@pytest.mark.e2e
def test_create_repo_invalid_payload(gitea_client: GiteaHttpClient):
    """
    Negative: creating a repository with invalid body (empty name) must fail.
    """
    # prepare user
    username = "invalid_payload_user"
    email = "invalid_payload@example.com"
    password = "Password123!"
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status in (422, 409)

    # try to create repo with invalid name (empty) - should fail
    r = gitea_client.create_repo(name="", private=False, description="should fail")
    assert not r.ok(), "Creating repo with empty name should fail"
    assert r.status in (400, 422), f"Expected validation error, got {r.status} {getattr(r,'text','')}"

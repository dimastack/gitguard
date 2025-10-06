import pytest


@pytest.mark.e2e
def test_repo_lifecycle(gitea_client):
    """
    Full repository lifecycle:
    1. create repository
    2. get repository details
    3. edit repository (change description)
    4. list repositories for user
    5. delete repository
    6. verify deletion
    """
    username = "testuser_repo"
    email = "testuser_repo@example.com"
    password = "Password123!"
    repo_name = "sample-repo"

    # Ensure user exists
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status_code in (409, 422), \
        f"Precondition failed: cannot ensure user exists ({r.status_code} {getattr(r,'text','')})"

    # Create repository
    r = gitea_client.create_repo(name=repo_name, owner=username, private=False, description="Initial repo")
    assert r.ok() or r.status_code == 409, f"Repo creation failed: {r.status_code} {getattr(r,'text','')}"
    repo_data = r.json if r.ok() else {}
    if r.ok():
        assert repo_data.get("name") == repo_name, f"Unexpected repo data: {repo_data}"

    # Get repository details
    r = gitea_client.get_repo(owner=username, repo=repo_name)
    assert r.ok(), f"Get repo failed: {r.status_code} {getattr(r,'text','')}"
    repo_info = r.json
    assert repo_info.get("name") == repo_name, f"Repo name mismatch: {repo_info}"
    assert repo_info.get("owner", {}).get("username") == username, \
        f"Repo owner mismatch: {repo_info.get('owner')}"

    # Edit repository description
    new_description = "Updated description"
    r = gitea_client.edit_repo(owner=username, repo=repo_name, description=new_description)
    assert r.ok(), f"Edit repo failed: {r.status_code} {getattr(r,'text','')}"
    r = gitea_client.get_repo(owner=username, repo=repo_name)
    assert r.ok(), f"Get after edit failed: {r.status_code}"
    assert r.json.get("description") == new_description, f"Repo description not updated: {r.json}"

    # List repositories for user
    r = gitea_client.list_user_repos(username)
    assert r.ok(), f"List user repos failed: {r.status_code} {getattr(r,'text','')}"
    repos = [repo.get("name") for repo in r.json]
    assert repo_name in repos, f"Expected repo '{repo_name}' in list: {repos}"

    # Delete repository
    r = gitea_client.delete_repo(owner=username, repo=repo_name)
    assert r.ok(), f"Delete repo failed: {r.status_code} {getattr(r,'text','')}"

    # Verify deletion
    r = gitea_client.get_repo(owner=username, repo=repo_name)
    assert not r.ok(), f"Deleted repo still exists: {r.status_code}"
    assert r.status_code == 404, f"Expected 404 after delete, got {r.status_code}"


@pytest.mark.e2e
def test_create_duplicate_repo(gitea_client):
    """
    Negative case: creating a repository with the same name twice should fail.
    """
    username = "dup_repo_user"
    email = "dup@example.com"
    password = "Password123!"
    repo_name = "dup-repo"

    # Ensure user exists
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status_code in (409, 422), \
        f"Precondition failed: cannot ensure user exists ({r.status_code} {getattr(r,'text','')})"

    # First creation (may already exist from prior run)
    r = gitea_client.create_repo(name=repo_name, owner=username)
    assert r.ok() or r.status_code in (409, 422), \
        f"First repo creation failed: {r.status_code} {getattr(r,'text','')}"

    # Second creation should fail (conflict)
    r = gitea_client.create_repo(name=repo_name, owner=username)
    assert not r.ok(), "Expected failure for duplicate repo creation"
    assert r.status_code in (409, 422), \
        f"Expected 409/422 for duplicate, got {r.status_code} {getattr(r,'text','')}"

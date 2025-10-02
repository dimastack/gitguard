import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.mark.e2e
def test_repo_lifecycle(gitea_client: GiteaHttpClient):
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

    # Ensure user exists (helper precondition)
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status_code == 422, f"Precondition: user creation failed {result.status_code} {result.text}"

    # 1. create repository
    result = gitea_client.create_repo(repo_name, owner=username, private=False, description="Initial repo")
    assert result.ok(), f"Repo creation failed: {result.status_code} {result.text}"
    repo_data = result.json()
    assert repo_data["name"] == repo_name, f"Expected repo {repo_name}, got {repo_data}"

    # 2. get repository details
    result = gitea_client.get_repo(owner=username, repo=repo_name)
    assert result.ok(), f"Get repo failed: {result.status_code} {result.text}"
    repo_info = result.json()
    assert repo_info["name"] == repo_name
    assert repo_info["owner"]["username"] == username

    # 3. edit repository description
    new_description = "Updated description"
    result = gitea_client.edit_repo(owner=username, repo=repo_name, description=new_description)
    assert result.ok(), f"Edit repo failed: {result.status_code} {result.text}"
    result = gitea_client.get_repo(owner=username, repo=repo_name)
    assert result.ok()
    assert result.json()["description"] == new_description, f"Repo description not updated: {result.json()}"

    # 4. list repositories for user
    result = gitea_client.list_user_repos(username)
    assert result.ok(), f"List user repos failed: {result.status_code} {result.text}"
    repos = [r["name"] for r in result.json()]
    assert repo_name in repos, f"Expected {repo_name} in {repos}"

    # 5. delete repository
    result = gitea_client.delete_repo(owner=username, repo=repo_name)
    assert result.ok(), f"Delete repo failed: {result.status_code} {result.text}"

    # 6. verify deletion
    result = gitea_client.get_repo(owner=username, repo=repo_name)
    assert not result.ok(), f"Deleted repo {repo_name} should not exist"
    assert result.status_code == 404, f"Expected 404 after deletion, got {result.status_code}"


@pytest.mark.e2e
def test_create_duplicate_repo(gitea_client: GiteaHttpClient):
    """
    Negative case: creating a repository with the same name twice should fail.
    """
    username = "dup_repo_user"
    email = "dup@example.com"
    password = "Password123!"
    repo_name = "dup-repo"

    # Ensure user exists
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status_code == 422

    # First creation should succeed
    result = gitea_client.create_repo(repo_name, owner=username)
    assert result.ok() or result.status_code == 409

    # Second creation should fail (conflict)
    result = gitea_client.create_repo(repo_name, owner=username)
    assert not result.ok(), f"Expected conflict, got {result.status_code}"
    assert result.status_code in (409, 422), f"Expected 409/422, got {result.status_code} {result.text}"

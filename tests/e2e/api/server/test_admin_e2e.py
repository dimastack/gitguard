import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.mark.e2e
def test_admin_create_edit_delete_user(gitea_client: GiteaHttpClient):
    """
    Full admin user lifecycle:
    1. create new user as admin
    2. verify in list_users
    3. edit user (update email)
    4. delete user
    5. confirm deletion
    """

    username = "admin_testuser"
    email = "admin_test@example.com"
    password = "Password123!"

    # 1. create new user
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status == 422, f"User creation failed: {result.status} {result.text}"

    # 2. verify in list_users
    result = gitea_client.list_users()
    assert result.ok(), f"List users failed: {result.status} {result.text}"
    usernames = [u["username"] for u in result.json()]
    assert username in usernames, f"Expected {username} in {usernames}"

    # 3. edit user email
    new_email = "admin_updated@example.com"
    result = gitea_client.edit_user(username, email=new_email)
    assert result.ok(), f"Edit user failed: {result.status} {result.text}"
    user_data = gitea_client.get_user(username).json()
    assert user_data["email"] == new_email, f"Email not updated, got {user_data}"

    # 4. delete user
    result = gitea_client.delete_user(username)
    assert result.ok(), f"Delete user failed: {result.status} {result.text}"

    # 5. confirm deletion
    result = gitea_client.get_user(username)
    assert not result.ok(), f"Expected user {username} to be deleted"
    assert result.status == 404, f"Expected 404, got {result.status}"


@pytest.mark.e2e
def test_admin_create_repo_for_user(gitea_client: GiteaHttpClient):
    """
    Admin repository lifecycle:
    1. create new user
    2. create repo for this user
    3. fetch repo
    """

    username = "admin_repo_owner"
    email = "repo_owner@example.com"
    password = "Password123!"
    repo_name = "admin-test-repo"

    # 1. create user if not exists
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status == 422

    # 2. create repo
    result = gitea_client.admin_create_repo(username=username, repo_name=repo_name)
    assert result.ok() or result.status == 409, f"Repo creation failed: {result.status} {result.text}"
    repo_data = result.json() if result.ok() else {}
    if result.ok():
        assert repo_data["name"] == repo_name, f"Unexpected repo name: {repo_data}"

    # 3. fetch repo
    result = gitea_client.get_repo(owner=username, repo=repo_name)
    assert result.ok(), f"Fetch repo failed: {result.status} {result.text}"
    fetched_repo = result.json()
    assert fetched_repo["name"] == repo_name, f"Expected repo {repo_name}, got {fetched_repo}"


@pytest.mark.e2e
def test_admin_list_unadopted_repos(gitea_client: GiteaHttpClient):
    """
    Admin unadopted repos endpoint should return valid JSON.
    """

    result = gitea_client.list_unadopted_repos()
    assert result.ok(), f"List unadopted repos failed: {result.status} {result.text}"
    data = result.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"


@pytest.mark.e2e
def test_admin_duplicate_user_creation(gitea_client: GiteaHttpClient):
    """
    Negative case: creating the same user twice should fail second time.
    """

    username = "dup_admin_user"
    email = "dup_admin@example.com"
    password = "Password123!"

    # First attempt
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status == 422

    # Second attempt must fail
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert not result.ok(), "Expected failure for duplicate user creation"
    assert result.status in (409, 422), f"Expected 409/422, got {result.status} {result.text}"

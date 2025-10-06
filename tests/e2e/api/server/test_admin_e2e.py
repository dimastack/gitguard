import pytest


@pytest.mark.e2e
def test_admin_create_edit_delete_user(gitea_client):
    """
    Full admin user lifecycle:
    1. Create new user as admin
    2. Verify in list_users
    3. Edit user (update email)
    4. Delete user
    5. Confirm deletion
    """

    username = "admin_testuser"
    email = "admin_test@example.com"
    password = "Password123!"

    # 1. Create new user
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code == 422, f"User creation failed: {resp.status_code} {resp.text}"

    # 2. Verify in list_users
    users = gitea_client.list_users()
    assert users.ok(), f"List users failed: {users.status_code} {users.text}"
    usernames = [u["username"] for u in users.json]
    assert username in usernames, f"Expected {username} in {usernames}"

    # 3. Edit user email
    new_email = "admin_updated@example.com"
    resp = gitea_client.edit_user(username, email=new_email)
    assert resp.ok(), f"Edit user failed: {resp.status_code} {resp.text}"
    user_data = gitea_client.get_user(username).json
    assert user_data["email"] == new_email, f"Email not updated, got {user_data}"

    # 4. Delete user
    resp = gitea_client.delete_user(username)
    assert resp.ok(), f"Delete user failed: {resp.status_code} {resp.text}"

    # 5. Confirm deletion
    resp = gitea_client.get_user(username)
    assert not resp.ok(), f"Expected user {username} to be deleted"
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


@pytest.mark.e2e
def test_admin_create_repo_for_user(gitea_client):
    """
    Admin repository lifecycle:
    1. Create new user
    2. Create repo for this user
    3. Fetch repo
    """

    username = "admin_repo_owner"
    email = "repo_owner@example.com"
    password = "Password123!"
    repo_name = "admin-test-repo"

    # 1. Create user if not exists
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code == 422, f"User creation failed: {resp.status_code} {resp.text}"

    # 2. Create repo
    resp = gitea_client.admin_create_repo(username=username, repo_name=repo_name)
    assert resp.ok() or resp.status_code == 409, f"Repo creation failed: {resp.status_code} {resp.text}"
    if resp.ok():
        repo_data = resp.json
        assert repo_data["name"] == repo_name, f"Unexpected repo name: {repo_data}"

    # 3. Fetch repo
    resp = gitea_client.get_repo(owner=username, repo=repo_name)
    assert resp.ok(), f"Fetch repo failed: {resp.status_code} {resp.text}"
    repo_data = resp.json
    assert repo_data["name"] == repo_name, f"Expected repo {repo_name}, got {repo_data}"


@pytest.mark.e2e
def test_admin_list_unadopted_repos(gitea_client):
    """Admin unadopted repos endpoint should return valid JSON."""
    resp = gitea_client.list_unadopted_repos()
    assert resp.ok(), f"List unadopted repos failed: {resp.status_code} {resp.text}"
    data = resp.json
    assert isinstance(data, list), f"Expected list, got {type(data)}"


@pytest.mark.e2e
def test_admin_duplicate_user_creation(gitea_client):
    """Negative case: creating the same user twice should fail the second time."""
    username = "dup_admin_user"
    email = "dup_admin@example.com"
    password = "Password123!"

    # First attempt
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code == 422

    # Second attempt must fail
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert not resp.ok(), "Expected failure for duplicate user creation"
    assert resp.status_code in (409, 422), f"Expected 409/422, got {resp.status_code} {resp.text}"

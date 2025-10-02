import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.mark.e2e
def test_user_lifecycle(gitea_client: GiteaHttpClient):
    """
    Full user lifecycle:
    1. create new user
    2. fetch user by username
    3. edit user (email change)
    4. list users and check presence
    5. delete user
    6. verify deletion
    """

    username = "testuser"
    email = "testuser@example.com"
    password = "Password123!"

    # 1. create user
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok(), f"User creation failed: {result.status} {result.text}"

    # 2. fetch user
    result = gitea_client.get_user(username)
    assert result.ok(), f"Get user failed: {result.status} {result.text}"
    data = result.json()
    assert data["username"] == username, f"Expected username {username}, got {data}"
    assert data["email"] == email, f"Expected email {email}, got {data}"

    # 3. edit user email
    new_email = "updated@example.com"
    result = gitea_client.edit_user(username, email=new_email)
    assert result.ok(), f"Edit user failed: {result.status} {result.text}"
    result = gitea_client.get_user(username)
    assert result.ok(), f"Re-fetch user after edit failed: {result.status} {result.text}"
    assert result.json()["email"] == new_email, f"Email not updated: {result.json()}"

    # 4. list users
    result = gitea_client.list_users()
    assert result.ok(), f"List users failed: {result.status} {result.text}"
    usernames = [u["username"] for u in result.json()]
    assert username in usernames, f"Expected {username} in {usernames}"

    # 5. delete user
    result = gitea_client.delete_user(username)
    assert result.ok(), f"Delete user failed: {result.status} {result.text}"

    # 6. verify deletion
    result = gitea_client.get_user(username)
    assert not result.ok(), f"Deleted user {username} should not exist"
    assert result.status == 404, f"Expected 404 after deletion, got {result.status}"


@pytest.mark.e2e
def test_get_nonexistent_user(gitea_client: GiteaHttpClient):
    """
    Negative case: requesting a non-existent user should return 404.
    """
    result = gitea_client.get_user("doesnotexist123")
    assert not result.ok(), "Expected failure for non-existing user"
    assert result.status == 404, f"Expected 404, got {result.status} {result.text}"

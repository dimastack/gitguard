import pytest


@pytest.mark.e2e
def test_user_lifecycle(gitea_client):
    """
    Full user lifecycle:
    1. create user
    2. get user details
    3. update user (email)
    4. list users
    5. delete user
    6. verify deletion
    """

    username = "e2e_test_user"
    email = "e2e_user@example.com"
    password = "Password123!"

    # Create user (handle already-exists gracefully)
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status_code in (409, 422), f"Create user failed: {r.status_code} {getattr(r,'text','')}"

    # Get user details
    r = gitea_client.get_user(username)
    assert r.ok(), f"Get user failed: {r.status_code} {getattr(r,'text','')}"
    user_data = r.json
    assert user_data.get("username") == username, f"Expected username '{username}', got {user_data}"

    # Update user email
    new_email = "updated_e2e_user@example.com"
    r = gitea_client.edit_user(username=username, email=new_email)
    assert r.ok(), f"Edit user failed: {r.status_code} {getattr(r,'text','')}"
    r = gitea_client.get_user(username)
    assert r.ok()
    assert r.json.get("email") == new_email, f"Email not updated: {r.json}"

    # List users and confirm presence
    r = gitea_client.list_users()
    assert r.ok(), f"List users failed: {r.status_code} {getattr(r,'text','')}"
    users = [u.get("username") for u in r.json]
    assert username in users, f"Expected {username} in user list: {users}"

    # Delete user
    r = gitea_client.delete_user(username)
    assert r.ok(), f"Delete user failed: {r.status_code} {getattr(r,'text','')}"

    # Verify deletion
    r = gitea_client.get_user(username)
    assert not r.ok(), f"User still exists after deletion: {r.status_code}"
    assert r.status_code == 404, f"Expected 404 after delete, got {r.status_code}"


@pytest.mark.e2e
def test_create_duplicate_user(gitea_client):
    """
    Negative case: creating a user with the same username twice should fail.
    """

    username = "dup_user_e2e"
    email = "dup_user_e2e@example.com"
    password = "Password123!"

    # First creation (might already exist)
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert r.ok() or r.status_code in (409, 422), f"First create failed: {r.status_code} {getattr(r,'text','')}"

    # Second creation should fail
    r = gitea_client.create_user(username=username, email=email, password=password)
    assert not r.ok(), "Expected failure for duplicate user creation"
    assert r.status_code in (409, 422), f"Expected 409/422, got {r.status_code} {getattr(r,'text','')}"


@pytest.mark.e2e
def test_get_nonexistent_user(gitea_client):
    """
    Negative case: fetching a non-existent user should return 404.
    """

    username = "ghost_user_xyz"
    r = gitea_client.get_user(username)
    assert not r.ok(), f"Expected 404 for non-existent user, got {r.status_code}"
    assert r.status_code == 404, f"Expected 404, got {r.status_code} {getattr(r,'text','')}"

import pytest


@pytest.mark.unit
def test_list_users(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value=[{"username": "bob"}])

    result = gitea_client.list_users()

    assert {"username": "bob"} in result
    mock_get.assert_called_once_with("admin/users", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_create_user(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"username": "bob"})

    result = gitea_client.create_user("bob", "bob@example.com", "pass")

    assert result["username"] == "bob"
    mock_post.assert_called_once_with(
        "admin/users",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "pass",
            "must_change_password": False,
        },
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_delete_user(mocker, gitea_client):
    mock_delete = mocker.patch.object(type(gitea_client), "delete", return_value={"result": "deleted"})

    result = gitea_client.delete_user("bob")

    assert result["result"] == "deleted"
    mock_delete.assert_called_once_with("admin/users/bob", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_edit_user(mocker, gitea_client):
    mock_patch = mocker.patch.object(type(gitea_client), "patch", return_value={"username": "bob", "active": False})

    result = gitea_client.edit_user("bob", active=False)

    assert result["active"] is False
    mock_patch.assert_called_once_with(
        "admin/users/bob",
        json={"active": False},
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_admin_create_org(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"full_name": "org1"})

    result = gitea_client.admin_create_org("alice", "org1", "desc")

    assert result["full_name"] == "org1"
    mock_post.assert_called_once_with(
        "admin/users/alice/orgs",
        json={"username": "alice", "full_name": "org1", "description": "desc"},
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_admin_create_repo(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"name": "repo1"})

    result = gitea_client.admin_create_repo("alice", "repo1", private=True)

    assert result["name"] == "repo1"
    mock_post.assert_called_once_with(
        "admin/users/alice/repos",
        json={"name": "repo1", "private": True},
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_list_unadopted_repos(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value=[{"repo_name": "lostrepo"}])

    result = gitea_client.list_unadopted_repos()

    assert {"repo_name": "lostrepo"} in result
    mock_get.assert_called_once_with("admin/unadopted", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_adopt_unadopted_repo(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"status": "adopted"})

    result = gitea_client.adopt_unadopted_repo("alice", "repo1")

    assert result["status"] == "adopted"
    mock_post.assert_called_once_with(
        "admin/unadopted",
        json={"repo_name": "repo1", "owner": "alice"},
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_delete_unadopted_repo(mocker, gitea_client):
    mock_delete = mocker.patch.object(type(gitea_client), "delete", return_value={"status": "deleted"})

    result = gitea_client.delete_unadopted_repo("alice", "repo1")

    assert result["status"] == "deleted"
    mock_delete.assert_called_once_with(
        "admin/unadopted/alice/repo1",
        headers=gitea_client._auth_headers(),
    )

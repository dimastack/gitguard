import pytest

from gitguard.clients.http_gitea_client import GiteaHttpClient


@pytest.mark.unit
def test_list_users(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value=[{"username": "bob"}])
    client = GiteaHttpClient("http://gitea.local")

    result = client.list_users()

    assert {"username": "bob"} in result
    mock_get.assert_called_once_with("admin/users", headers=client._auth_headers())


@pytest.mark.unit
def test_create_user(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"username": "bob"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.create_user("bob", "bob@example.com", "pass")

    assert result["username"] == "bob"
    mock_post.assert_called_once_with(
        "admin/users",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "pass",
            "must_change_password": False,
        },
        headers=client._auth_headers(),
    )


@pytest.mark.unit
def test_delete_user(mocker):
    mock_delete = mocker.patch.object(GiteaHttpClient, "delete", return_value={"result": "deleted"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.delete_user("bob")

    assert result["result"] == "deleted"
    mock_delete.assert_called_once_with("admin/users/bob", headers=client._auth_headers())


@pytest.mark.unit
def test_edit_user(mocker):
    mock_patch = mocker.patch.object(GiteaHttpClient, "patch", return_value={"username": "bob", "active": False})
    client = GiteaHttpClient("http://gitea.local")

    result = client.edit_user("bob", active=False)

    assert result["active"] is False
    mock_patch.assert_called_once_with(
        "admin/users/bob",
        json={"active": False},
        headers=client._auth_headers(),
    )


@pytest.mark.unit
def test_admin_create_org(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"full_name": "org1"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.admin_create_org("alice", "org1", "desc")

    assert result["full_name"] == "org1"
    mock_post.assert_called_once_with(
        "admin/users/alice/orgs",
        json={"username": "alice", "full_name": "org1", "description": "desc"},
        headers=client._auth_headers(),
    )


@pytest.mark.unit
def test_admin_create_repo(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"name": "repo1"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.admin_create_repo("alice", "repo1", private=True)

    assert result["name"] == "repo1"
    mock_post.assert_called_once_with(
        "admin/users/alice/repos",
        json={"name": "repo1", "private": True},
        headers=client._auth_headers(),
    )


@pytest.mark.unit
def test_list_unadopted_repos(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value=[{"repo_name": "lostrepo"}])
    client = GiteaHttpClient("http://gitea.local")

    result = client.list_unadopted_repos()

    assert {"repo_name": "lostrepo"} in result
    mock_get.assert_called_once_with("admin/unadopted", headers=client._auth_headers())


@pytest.mark.unit
def test_adopt_unadopted_repo(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"status": "adopted"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.adopt_unadopted_repo("alice", "repo1")

    assert result["status"] == "adopted"
    mock_post.assert_called_once_with(
        "admin/unadopted",
        json={"repo_name": "repo1", "owner": "alice"},
        headers=client._auth_headers(),
    )


@pytest.mark.unit
def test_delete_unadopted_repo(mocker):
    mock_delete = mocker.patch.object(GiteaHttpClient, "delete", return_value={"status": "deleted"})
    client = GiteaHttpClient("http://gitea.local")

    result = client.delete_unadopted_repo("alice", "repo1")

    assert result["status"] == "deleted"
    mock_delete.assert_called_once_with(
        "admin/unadopted/alice/repo1",
        headers=client._auth_headers(),
    )

import pytest


@pytest.mark.unit
def test_get_user_success(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value={"username": "alice"})

    result = gitea_client.get_user("alice")

    assert result["username"] == "alice"
    mock_get.assert_called_once_with("users/alice", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_get_user_not_found(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value={"message": "user not found"})

    result = gitea_client.get_user("ghost")

    assert "user not found" in result["message"]
    mock_get.assert_called_once_with("users/ghost", headers=gitea_client._auth_headers())

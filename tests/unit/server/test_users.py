import pytest

from clients.http_gitea_client import GiteaHttpClient

@pytest.mark.unit
def test_get_user_success(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value={"username": "alice"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.get_user("alice")
    assert result["username"] == "alice"
    mock_get.assert_called_once_with("users/alice", headers=client._auth_headers())

@pytest.mark.unit
def test_get_user_not_found(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value={"message": "user not found"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.get_user("ghost")
    assert "user not found" in result["message"]

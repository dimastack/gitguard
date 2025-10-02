import pytest
from gitguard.clients.http_gitea_client import GiteaHttpClient

@pytest.mark.unit
def test_create_repo_success(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"name": "repo1"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.create_repo("repo1", private=True)
    assert result["name"] == "repo1"
    mock_post.assert_called_once_with(
        "user/repos",
        json={"name": "repo1", "private": True, "description": ""},
        headers=client._auth_headers()
    )

@pytest.mark.unit
def test_delete_repo(mocker):
    mock_delete = mocker.patch.object(GiteaHttpClient, "delete", return_value={"result": "deleted"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.delete_repo("alice", "repo1")
    assert result["result"] == "deleted"
    mock_delete.assert_called_once_with("repos/alice/repo1", headers=client._auth_headers())

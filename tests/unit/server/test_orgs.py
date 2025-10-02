import pytest
from clients.http_gitea_client import GiteaHttpClient


@pytest.mark.unit
def test_list_orgs(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value=[{"full_name": "org1"}])
    client = GiteaHttpClient("http://gitea.local")
    result = client.list_orgs()
    assert {"full_name": "org1"} in result
    mock_get.assert_called_once_with("user/orgs", headers=client._auth_headers())


@pytest.mark.unit
def test_create_org(mocker):
    mock_post = mocker.patch.object(GiteaHttpClient, "post", return_value={"full_name": "testorg"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.create_org("testorg", "desc")
    assert result["full_name"] == "testorg"
    mock_post.assert_called_once()

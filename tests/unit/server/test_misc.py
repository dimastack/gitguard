import pytest

from clients.http_gitea_client import GiteaHttpClient


@pytest.mark.unit
def test_health_check(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value={"status": "ok"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.health_check()
    assert result["status"] == "ok"
    mock_get.assert_called_once_with("", headers=client._auth_headers())


@pytest.mark.unit
def test_version(mocker):
    mock_get = mocker.patch.object(GiteaHttpClient, "get", return_value={"version": "1.20.3"})
    client = GiteaHttpClient("http://gitea.local")
    result = client.version()
    assert result["version"] == "1.20.3"
    mock_get.assert_called_once_with("version", headers=client._auth_headers())

import pytest


@pytest.mark.unit
def test_health_check(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value={"status": "ok"})

    result = gitea_client.health_check()

    assert result["status"] == "ok"
    mock_get.assert_called_once_with("", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_version(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value={"version": "1.20.3"})

    result = gitea_client.version()

    assert result["version"] == "1.20.3"
    mock_get.assert_called_once_with("version", headers=gitea_client._auth_headers())

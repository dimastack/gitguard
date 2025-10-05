import pytest


@pytest.mark.unit
def test_list_orgs(mocker, gitea_client):
    mock_get = mocker.patch.object(type(gitea_client), "get", return_value=[{"full_name": "org1"}])

    result = gitea_client.list_orgs()

    assert {"full_name": "org1"} in result
    mock_get.assert_called_once_with("user/orgs", headers=gitea_client._auth_headers())


@pytest.mark.unit
def test_create_org(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"full_name": "testorg"})

    result = gitea_client.create_org("testorg", "desc")

    assert result["full_name"] == "testorg"
    mock_post.assert_called_once_with(
        "orgs",
        json={"username": "testorg", "full_name": "testorg", "description": "desc"},
        headers=gitea_client._auth_headers(),
    )

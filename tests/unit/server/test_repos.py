import pytest


@pytest.mark.unit
def test_create_repo_success(mocker, gitea_client):
    mock_post = mocker.patch.object(type(gitea_client), "post", return_value={"name": "repo1"})

    result = gitea_client.create_repo("repo1", private=True)

    assert result["name"] == "repo1"
    mock_post.assert_called_once_with(
        "user/repos",
        json={"name": "repo1", "private": True, "description": ""},
        headers=gitea_client._auth_headers(),
    )


@pytest.mark.unit
def test_delete_repo(mocker, gitea_client):
    mock_delete = mocker.patch.object(type(gitea_client), "delete", return_value={"result": "deleted"})

    result = gitea_client.delete_repo("alice", "repo1")

    assert result["result"] == "deleted"
    mock_delete.assert_called_once_with(
        "repos/alice/repo1",
        headers=gitea_client._auth_headers(),
    )

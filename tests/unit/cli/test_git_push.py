import pytest


@pytest.mark.unit
def test_push_success(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Pushed"
    mock_run.return_value.stderr = ""

    result = git_client.push(str(git_client.workdir))

    assert result.returncode == 0
    assert "Pushed" in result.stdout


@pytest.mark.unit
def test_push_rejected(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "[rejected] main -> main (fetch first)"

    result = git_client.push(str(git_client.workdir))

    assert result.returncode == 1
    assert "rejected" in result.stderr


@pytest.mark.unit
def test_push_permission_denied(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = (
        "fatal: Authentication failed for 'http://example.com/repo.git/'"
    )

    result = git_client.push(str(git_client.workdir))

    assert result.returncode == 128
    assert "Authentication failed" in result.stderr


@pytest.mark.unit
def test_push_not_a_repo(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: not a git repository"

    result = git_client.push(str(git_client.workdir))

    assert result.returncode == 128
    assert "not a git repository" in result.stderr


@pytest.mark.unit
def test_push_timeout(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=TimeoutError("push timed out"))

    with pytest.raises(TimeoutError):
        git_client.push(str(git_client.workdir))


@pytest.mark.unit
def test_push_git_not_found(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    with pytest.raises(OSError):
        git_client.push(str(git_client.workdir))

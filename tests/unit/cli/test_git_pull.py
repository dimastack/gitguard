import pytest


@pytest.mark.unit
def test_pull_success(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Already up to date."
    mock_run.return_value.stderr = ""

    result = git_client.pull(str(git_client.workdir))

    assert result.returncode == 0
    assert "Already up to date" in result.stdout


@pytest.mark.unit
def test_pull_conflict(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "CONFLICT (content): Merge conflict"

    result = git_client.pull(str(git_client.workdir))

    assert result.returncode == 1
    assert "CONFLICT" in result.stderr


@pytest.mark.unit
def test_pull_not_a_repo(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: not a git repository"

    result = git_client.pull(str(git_client.workdir))

    assert result.returncode == 128
    assert "not a git repository" in result.stderr


@pytest.mark.unit
def test_pull_timeout(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=TimeoutError("pull timed out"))

    with pytest.raises(TimeoutError):
        git_client.pull(str(git_client.workdir))


@pytest.mark.unit
def test_pull_git_not_found(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    with pytest.raises(OSError):
        git_client.pull(str(git_client.workdir))

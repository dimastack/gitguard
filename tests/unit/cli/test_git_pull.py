import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.unit
def test_pull_success(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Already up to date."
    mock_run.return_value.stderr = ""

    client = GitClient(protocol="http")
    result = client.pull("/tmp/repo")

    assert result.returncode == 0
    assert "Already up to date" in result.stdout


@pytest.mark.unit
def test_pull_conflict(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "CONFLICT (content): Merge conflict"

    client = GitClient(protocol="http")
    result = client.pull("/tmp/repo")

    assert result.returncode == 1
    assert "CONFLICT" in result.stderr


@pytest.mark.unit
def test_pull_not_a_repo(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: not a git repository"

    client = GitClient(protocol="http")
    result = client.pull("/tmp/not_a_repo")

    assert result.returncode == 128
    assert "not a git repository" in result.stderr


@pytest.mark.unit
def test_pull_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=TimeoutError("pull timed out"))

    client = GitClient(protocol="http")
    with pytest.raises(TimeoutError):
        client.pull("/tmp/repo")


@pytest.mark.unit
def test_pull_git_not_found(mocker):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    client = GitClient(protocol="http")
    with pytest.raises(OSError):
        client.pull("/tmp/repo")

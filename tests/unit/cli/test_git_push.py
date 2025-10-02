import pytest
from clients.git_client import GitClient


@pytest.mark.unit
def test_push_success(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Pushed"
    mock_run.return_value.stderr = ""

    client = GitClient(protocol="http")
    result = client.push("/tmp/repo")

    assert result.returncode == 0
    assert "Pushed" in result.stdout


@pytest.mark.unit
def test_push_rejected(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "[rejected] main -> main (fetch first)"

    client = GitClient(protocol="http")
    result = client.push("/tmp/repo")

    assert result.returncode == 1
    assert "rejected" in result.stderr


@pytest.mark.unit
def test_push_permission_denied(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: Authentication failed for 'http://example.com/repo.git/'"

    client = GitClient(protocol="http")
    result = client.push("/tmp/repo")

    assert result.returncode == 128
    assert "Authentication failed" in result.stderr


@pytest.mark.unit
def test_push_not_a_repo(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: not a git repository"

    client = GitClient(protocol="http")
    result = client.push("/tmp/not_a_repo")

    assert result.returncode == 128
    assert "not a git repository" in result.stderr


@pytest.mark.unit
def test_push_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=TimeoutError("push timed out"))

    client = GitClient(protocol="http")
    with pytest.raises(TimeoutError):
        client.push("/tmp/repo")


@pytest.mark.unit
def test_push_git_not_found(mocker):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    client = GitClient(protocol="http")
    with pytest.raises(OSError):
        client.push("/tmp/repo")

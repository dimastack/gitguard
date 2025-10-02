import pytest
from clients.git_client import GitClient

@pytest.mark.unit
def test_clone_success(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Cloned"
    mock_run.return_value.stderr = ""

    client = GitClient(protocol="http")
    result = client.clone("http://example.com/repo.git", "/tmp/repo")

    assert result.returncode == 0
    assert "Cloned" in result.stdout

@pytest.mark.unit
def test_clone_failure(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: repository not found"

    client = GitClient(protocol="http")
    result = client.clone("http://invalid/repo.git", "/tmp/repo")

    assert result.returncode == 128
    assert "fatal" in result.stderr


@pytest.mark.unit
def test_clone_timeout(mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=TimeoutError("Command timed out"))

    client = GitClient(protocol="http")
    with pytest.raises(TimeoutError):
        client.clone("http://example.com/repo.git", "/tmp/repo")


@pytest.mark.unit
def test_clone_oserror(mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=OSError("No such file or directory"))

    client = GitClient(protocol="http")
    with pytest.raises(OSError):
        client.clone("http://example.com/repo.git", "/tmp/repo")


@pytest.mark.unit
def test_clone_invalid_url(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: unable to access 'http://': Invalid URL"

    client = GitClient(protocol="http")
    result = client.clone("http://", "/tmp/repo")

    assert result.returncode == 128
    assert "Invalid URL" in result.stderr

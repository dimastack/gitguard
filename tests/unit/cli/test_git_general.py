import pytest

from gitguard.clients.git_client import GitClient


@pytest.mark.unit
def test_init_repo(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Initialized empty Git repo"
    mock_run.return_value.stderr = ""

    client = GitClient(protocol="http")
    result = client.init("/tmp/repo")

    assert result.returncode == 0
    assert "Initialized" in result.stdout


@pytest.mark.unit
def test_init_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=TimeoutError("init timed out"))

    client = GitClient(protocol="http")
    with pytest.raises(TimeoutError):
        client.init("/tmp/repo")


@pytest.mark.unit
def test_init_permission_error(mocker):
    mocker.patch("subprocess.run", side_effect=PermissionError("Permission denied"))

    client = GitClient(protocol="http")
    with pytest.raises(PermissionError):
        client.init("/restricted/repo")


@pytest.mark.unit
def test_switch_branch_failure(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "error: pathspec 'nonexistent' did not match any file(s) known to git"

    client = GitClient(protocol="http")
    result = client.switch("/tmp/repo", "nonexistent")

    assert result.returncode == 1
    assert "pathspec" in result.stderr


@pytest.mark.unit
def test_switch_branch_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=TimeoutError("checkout timed out"))

    client = GitClient(protocol="http")
    with pytest.raises(TimeoutError):
        client.switch("/tmp/repo", "feature/timeout")


def test_switch_oserror(mocker):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    client = GitClient(protocol="http")
    with pytest.raises(OSError):
        client.switch("/tmp/repo", "develop")


@pytest.mark.unit
def test_switch_invalid_branch(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: invalid reference: '***'"

    client = GitClient(protocol="http")
    result = client.switch("/tmp/repo", "***")

    assert result.returncode == 1
    assert "invalid reference" in result.stderr

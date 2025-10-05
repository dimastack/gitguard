import pytest


@pytest.mark.unit
def test_init_repo(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Initialized empty Git repo"
    mock_run.return_value.stderr = ""

    result = git_client.init(str(git_client.workdir))

    assert result.returncode == 0
    assert "Initialized" in result.stdout


@pytest.mark.unit
def test_init_timeout(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=TimeoutError("init timed out"))

    with pytest.raises(TimeoutError):
        git_client.init(str(git_client.workdir))


@pytest.mark.unit
def test_init_permission_error(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=PermissionError("Permission denied"))

    with pytest.raises(PermissionError):
        git_client.init("/restricted/repo")


@pytest.mark.unit
def test_checkout_branch_failure(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "error: pathspec 'nonexistent' did not match any file(s) known to git"

    result = git_client.checkout(str(git_client.workdir), "nonexistent")

    assert result.returncode == 1
    assert "pathspec" in result.stderr


@pytest.mark.unit
def test_checkout_branch_timeout(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=TimeoutError("checkout timed out"))

    with pytest.raises(TimeoutError):
        git_client.checkout(str(git_client.workdir), "feature/timeout")


def test_checkout_oserror(mocker, git_client):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))

    with pytest.raises(OSError):
        git_client.checkout(str(git_client.workdir), "develop")


@pytest.mark.unit
def test_checkout_invalid_branch(mocker, git_client):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "fatal: invalid reference: '***'"

    result = git_client.checkout(str(git_client.workdir), "***")

    assert result.returncode == 1
    assert "invalid reference" in result.stderr

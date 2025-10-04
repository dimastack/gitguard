# clients/git_client.py
from __future__ import annotations

import subprocess
import os
import time
import datetime
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

try:
    import allure
    _HAS_ALLURE = True
except Exception:
    _HAS_ALLURE = False

# Single named logger for the whole project (configure it centrally)
logger = logging.getLogger("gitguard")


@dataclass
class GitResult:
    """Result of a git command."""
    code: int
    stdout: str
    stderr: str
    duration: float  # seconds

    # keep old name `code` and provide `returncode` alias for tests
    @property
    def returncode(self) -> int:
        return self.code

    def ok(self) -> bool:
        return self.code == 0


class GitClient:
    """
    Thin wrapper around the system `git` command used by tests.

    Construction:
        GitClient(protocol="ssh", host="gitea", owner="alice", repo="demo", workdir="/workspace")

    Behavior:
    - Builds repo URLs from protocol/host/owner/repo when repo_url is not provided.
    - Enables internal git trace logs (GIT_TRACE, GIT_CURL_VERBOSE, ssh -v) by default.
    - Writes per-run artifact log to `artifacts/git-<timestamp>.log`.
    - Attaches the log to Allure after each command (if Allure is available).
    """

    def __init__(
        self,
        protocol: str = "http",
        host: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        workdir: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        enable_trace: bool = True,
        attach_logs_always: bool = True,
    ):
        self.protocol = (protocol or "http").lower()
        self.host = host
        self.owner = owner
        self.repo = repo
        self.workdir = Path(workdir) if workdir else Path.cwd()
        self.enable_trace = bool(enable_trace)
        self.attach_logs_always = bool(attach_logs_always)

        # artifacts dir (under workdir so CI picks it up easily)
        if artifacts_dir:
            self.artifacts = Path(artifacts_dir)
        else:
            self.artifacts = (self.workdir / "artifacts").resolve()
        self.artifacts.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.artifacts / f"git-client-{ts}.log"

        logger.debug(
            "Initialized GitClient: protocol=%s host=%s owner=%s repo=%s workdir=%s artifacts=%s",
            self.protocol,
            self.host,
            self.owner,
            self.repo,
            str(self.workdir),
            str(self.artifacts),
        )

    # -----------------------
    # URL builder / helpers
    # -----------------------
    def _make_repo_url(self, protocol: Optional[str] = None, host: Optional[str] = None,
                       owner: Optional[str] = None, repo: Optional[str] = None) -> str:
        """
        Build a repo URL using the client defaults unless explicit overrides are provided.
        Raises ValueError if owner/repo/host are missing.
        """
        proto = (protocol or self.protocol).lower()
        h = host or self.host
        o = owner or self.owner
        r = repo or self.repo

        if not (h and o and r):
            raise ValueError("host/owner/repo must be provided to build repository URL")

        repo_path = f"{o}/{r}.git"

        if proto in ("http", "https"):
            return f"{proto}://{h}/{repo_path}"
        if proto == "git":
            return f"git://{h}/{repo_path}"
        if proto == "ssh":
            return f"git@{h}:{repo_path}"
        raise ValueError(f"Unsupported protocol '{proto}'")

    def _write_log_header(self, cmd: List[str], env: dict, duration: float, rc: int, stdout: str, stderr: str) -> None:
        header = (
            f"\n---\nTime: {datetime.datetime.utcnow().isoformat()}Z\n"
            f"Workdir: {self.workdir}\n"
            f"Command: {shlex.join(cmd)}\n"
            f"Env (GIT_TRACE/GIT_CURL_VERBOSE/GIT_SSH_COMMAND): "
            f"{env.get('GIT_TRACE')} / {env.get('GIT_CURL_VERBOSE')} / {env.get('GIT_SSH_COMMAND')}\n"
            f"Return code: {rc}\n"
            f"Duration: {duration:.6f} sec\n"
            f"---\n"
        )
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(header)
                if stdout:
                    f.write("STDOUT:\n")
                    f.write(stdout + ("\n" if not stdout.endswith("\n") else ""))
                if stderr:
                    f.write("STDERR:\n")
                    f.write(stderr + ("\n" if not stderr.endswith("\n") else ""))
                f.flush()
        except Exception:
            logger.exception("Failed writing git-client log to %s", self.log_path)

    def _attach_log_to_allure(self, note: Optional[str] = None) -> None:
        if not self.attach_logs_always:
            return
        if not _HAS_ALLURE:
            logger.debug("Allure not available; skipping attaching log.")
            return
        try:
            name = f"git-client-log"
            if note:
                name = f"{name}-{note}"
            # attach the current log file content
            with open(self.log_path, "rb") as fh:
                allure.attach(fh.read(), name=name, attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            logger.exception("Failed to attach git client log to Allure: %s", e)

    # -----------------------
    # Core runner
    # -----------------------
    def _run(self, args: List[str], workdir: Optional[str] = None, extra_env: Optional[dict] = None) -> GitResult:
        """
        Run a git command with optional workdir and environment.
        Uses subprocess.run so tests can mock subprocess.run easily.
        Returns GitResult. Exceptions from subprocess.run (OSError, PermissionError, TimeoutError) are allowed to bubble up.
        """
        cmd = ["git"] + args
        logger.debug("About to run git command: %s", shlex.join(cmd))

        env = os.environ.copy()
        if extra_env:
            env.update({k: str(v) for k, v in extra_env.items()})

        if self.enable_trace:
            env.setdefault("GIT_TRACE", "1")
            env.setdefault("GIT_CURL_VERBOSE", "1")
            env.setdefault("GIT_SSH_COMMAND", "ssh -v")

        cwd = Path(workdir) if workdir else self.workdir

        start = time.perf_counter()
        # Use subprocess.run to make mocking easier in unit tests
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                check=False,
            )
        except Exception as exc:
            # write a brief log and re-raise so tests see exceptions (PermissionError/OSError/TimeoutError etc.)
            duration = time.perf_counter() - start
            try:
                self._write_log_header(cmd, env, duration, -1, "", str(exc))
                self._attach_log_to_allure()
            except Exception:
                logger.exception("Failed to log failed run")
            raise

        duration = time.perf_counter() - start
        rc = completed.returncode
        out = completed.stdout or ""
        err = completed.stderr or ""

        # write comprehensive log (best-effort)
        try:
            self._write_log_header(cmd, env, duration, rc, out, err)
        except Exception:
            logger.exception("Failed writing git-client log to %s", self.log_path)

        # attach log (best-effort)
        try:
            self._attach_log_to_allure()
        except Exception:
            logger.exception("Failed attaching log to Allure")

        return GitResult(code=rc, stdout=out.strip(), stderr=err.strip(), duration=duration)

    # -----------------------
    # Public operations
    # -----------------------

    def clone(self, target_dir: Optional[str] = None, repo_url: Optional[str] = None,
              protocol: Optional[str] = None, host: Optional[str] = None,
              owner: Optional[str] = None, repo: Optional[str] = None, workdir: Optional[str] = None) -> GitResult:
        """
        Clone repository. If repo_url is provided it is used verbatim;
        otherwise URL is constructed from protocol/host/owner/repo (overrides allowed).
        Accepts optional `workdir` to run inside.
        """
        if repo_url:
            url = repo_url
        else:
            url = self._make_repo_url(protocol=protocol, host=host, owner=owner, repo=repo)
        args = ["clone", url]
        if target_dir:
            args.append(target_dir)
        return self._run(args, workdir=workdir)

    def init(self, workdir: Optional[str] = None) -> GitResult:
        """Initialize a repository in workdir (or self.workdir if not provided)."""
        return self._run(["init"], workdir=workdir)

    def add(self, path: str = ".", workdir: Optional[str] = None) -> GitResult:
        return self._run(["add", path], workdir=workdir)

    def commit(self, message: str, workdir: Optional[str] = None) -> GitResult:
        # commit might fail if user.email/name not set — tests may set it earlier
        return self._run(["commit", "-m", message], workdir=workdir)

    def push(self, workdir: Optional[str] = None, remote: str = "origin", branch: str = "main") -> GitResult:
        """
        Push current branch. Accepts workdir as first argument (for backward compatibility tests that pass path first).
        Note: tests commonly call client.push("/tmp/repo"), so to keep compatibility the first positional is workdir.
        """
        return self._run(["push", remote, branch], workdir=workdir)

    def pull(self, workdir: Optional[str] = None, remote: str = "origin", branch: str = "main") -> GitResult:
        return self._run(["pull", remote, branch], workdir=workdir)

    def fetch(self, workdir: Optional[str] = None, remote: str = "origin") -> GitResult:
        return self._run(["fetch", remote], workdir=workdir)

    def status(self, workdir: Optional[str] = None) -> GitResult:
        return self._run(["status"], workdir=workdir)

    def checkout(self, branch: str, workdir: Optional[str] = None) -> GitResult:
        return self._run(["checkout", branch], workdir=workdir)

    def branch(self, name: str, workdir: Optional[str] = None) -> GitResult:
        return self._run(["branch", name], workdir=workdir)

    # alias expected in tests
    def switch(self, workdir: Optional[str], branch: str) -> GitResult:
        """
        Switch branch (compatibility wrapper).
        Tests call client.switch("/tmp/repo", "branch").
        """
        return self.checkout(branch, workdir=workdir)

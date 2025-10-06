from __future__ import annotations

import subprocess
import os
import time
import datetime
import logging
import shlex

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

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

    @property
    def returncode(self) -> int:
        return self.code

    def ok(self) -> bool:
        return self.code == 0


class GitClient:
    """
    Thin wrapper around the system `git` command used by tests.
    Features:
    - Logs all commands with timestamps, duration, env vars, stdout/stderr to a log
    - Uses subprocess.run(...) (so unit tests that patch subprocess.run work).
    - Public operations accept optional `workdir` override so tests can call client.pull("/tmp/repo").
    - Returns GitResult with `.returncode` property for compatibility.
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

        logger.debug("Initialized GitClient: protocol=%s host=%s owner=%s repo=%s workdir=%s artifacts=%s",
                     self.protocol, self.host, self.owner, self.repo, str(self.workdir), str(self.artifacts))

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
            port = 3000 if proto == "http" else 443
            return f"{proto}://{h}:{port}/{repo_path}"
        if proto == "git":
            port = 9418
            return f"{proto}://{h}:{port}/{repo_path}"
        if proto == "ssh":
            port = 2222
            return f"{proto}://git@{h}:{port}/{repo_path}"
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
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(header)
            if stdout:
                f.write("STDOUT:\n")
                f.write(stdout + ("\n" if not stdout.endswith("\n") else ""))
            if stderr:
                f.write("STDERR:\n")
                f.write(stderr + ("\n" if not stderr.endswith("\n") else ""))
            f.flush()

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

    # -----------
    # Core runner 
    # -----------
    def _run(self, args: List[str], extra_env: Optional[dict] = None, cwd: Optional[str] = None,
             timeout: Optional[float] = 60) -> GitResult:
        """
        Run a git command with optional extra environment and optional cwd override.
        Returns GitResult (and allows subprocess.run to be mocked by unit tests).
        """
        cmd = ["git"] + args
        logger.debug("About to run git command: %s", shlex.join(cmd))

        env = os.environ.copy()
        if extra_env:
            env.update({k: str(v) for k, v in extra_env.items()})

        if self.enable_trace:
            env.setdefault("GIT_TRACE", "1")
            env.setdefault("GIT_CURL_VERBOSE", "1")
            env.setdefault("GIT_SSH_COMMAND", 
                           "ssh -v -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null")

        # determine working directory
        run_cwd = str(self.workdir) if cwd is None else str(Path(cwd))

        start = time.perf_counter()
        try:
            completed = subprocess.run(
                cmd,
                cwd=run_cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=timeout,
                check=False,
            )
            out = completed.stdout or ""
            err = completed.stderr or ""
            rc = completed.returncode
        except (OSError, PermissionError) as e:
            duration = time.perf_counter() - start
            try:
                self._write_log_header(cmd, env, duration, 1, "", str(e))
            except Exception:
                logger.exception("Failed writing git-client log (exception path)")
            raise
        except subprocess.TimeoutExpired as e:
            duration = time.perf_counter() - start
            try:
                # e.stdout/e.stderr might be bytes or None
                stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
                stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
                self._write_log_header(cmd, env, duration, 124, stdout, stderr)
            except Exception:
                logger.exception("Failed writing git-client log (timeout path)")
            # Re-raise TimeoutError for tests expecting it
            raise TimeoutError(str(e)) from e
        finally:
            duration = time.perf_counter() - start

        # write comprehensive log
        try:
            self._write_log_header(cmd, env, duration, rc, out, err)
        except Exception:
            logger.exception("Failed writing git-client log to %s", self.log_path)

        # attach log (always if configured)
        try:
            self._attach_log_to_allure()
        except Exception:
            logger.exception("Failed attaching log to Allure")

        return GitResult(code=rc, stdout=out.strip(), stderr=err.strip(), duration=duration)

    # -------------------------------------------
    # Public operations (accept optional workdir)
    # -------------------------------------------   

    def clone(self, target_dir: Optional[str] = None, repo_url: Optional[str] = None,
              protocol: Optional[str] = None, host: Optional[str] = None,
              owner: Optional[str] = None, repo: Optional[str] = None,
              workdir: Optional[str] = None) -> GitResult:
        """
        Clone repository. If repo_url is provided it is used verbatim;
        otherwise URL is constructed from protocol/host/owner/repo (overrides allowed).
        """
        if repo_url:
            url = repo_url
        else:
            url = self._make_repo_url(protocol=protocol, host=host, owner=owner, repo=repo)
        args = ["clone", url]
        if target_dir:
            args.append(target_dir)
        return self._run(args, cwd=workdir)

    def init(self, path: Optional[str] = None, workdir: Optional[str] = None) -> GitResult:
        """
        git init [path]
        """
        args = ["init"]
        if path:
            args.append(path)
        return self._run(args, cwd=workdir)

    def add(self, path: str = ".", workdir: Optional[str] = None) -> GitResult:
        return self._run(["add", path], cwd=workdir)

    def commit(self, message: str, workdir: Optional[str] = None) -> GitResult:
        # commit might fail if user.email/name not set — tests may set it earlier
        return self._run(["commit", "-m", message], cwd=workdir)

    def push(self, remote: str = "origin", branch: str = "main", workdir: Optional[str] = None) -> GitResult:
        return self._run(["push", remote, branch], cwd=workdir)

    def pull(self, remote: str = "origin", branch: str = "main", workdir: Optional[str] = None) -> GitResult:
        return self._run(["pull", remote, branch], cwd=workdir)

    def fetch(self, remote: str = "origin", workdir: Optional[str] = None) -> GitResult:
        return self._run(["fetch", remote], cwd=workdir)

    def status(self, workdir: Optional[str] = None) -> GitResult:
        return self._run(["status"], cwd=workdir)

    def checkout(self, branch: str, workdir: Optional[str] = None) -> GitResult:
        return self._run(["checkout", branch], cwd=workdir)

    def branch(self, name: str, workdir: Optional[str] = None) -> GitResult:
        return self._run(["branch", name], cwd=workdir)

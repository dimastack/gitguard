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

logger = logging.getLogger("gitguard")


@dataclass
class GitResult:
    """Result of a git command."""
    code: int
    stdout: str
    stderr: str
    duration: float  # seconds

    def ok(self) -> bool:
        return self.code == 0


class GitClient:
    """
    Thin wrapper around the system `git` command used by tests.
    Provides convenience methods for core git operations.
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

    # -----------------------
    # Helpers
    # -----------------------

    def _make_repo_url(self, protocol: Optional[str] = None, host: Optional[str] = None,
                       owner: Optional[str] = None, repo: Optional[str] = None) -> str:
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

    def _write_log(self, cmd: List[str], env: dict, duration: float, rc: int, stdout: str, stderr: str) -> None:
        header = (
            f"\n---\nTime: {datetime.datetime.utcnow().isoformat()}Z\n"
            f"Workdir: {self.workdir}\n"
            f"Command: {shlex.join(cmd)}\n"
            f"Return code: {rc}\n"
            f"Duration: {duration:.6f} sec\n"
            f"---\n"
        )
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(header)
            if stdout:
                f.write("STDOUT:\n" + stdout + "\n")
            if stderr:
                f.write("STDERR:\n" + stderr + "\n")
            f.flush()

    def _attach_log_to_allure(self, note: Optional[str] = None) -> None:
        if not self.attach_logs_always or not _HAS_ALLURE:
            return
        try:
            name = "git-client-log" + (f"-{note}" if note else "")
            with open(self.log_path, "rb") as fh:
                allure.attach(fh.read(), name=name, attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            logger.exception("Failed to attach log to Allure: %s", e)

    def _run(self, args: List[str], extra_env: Optional[dict] = None) -> GitResult:
        cmd = ["git"] + args
        env = os.environ.copy()
        if extra_env:
            env.update({k: str(v) for k, v in extra_env.items()})
        if self.enable_trace:
            env.setdefault("GIT_TRACE", "1")
            env.setdefault("GIT_CURL_VERBOSE", "1")
            env.setdefault("GIT_SSH_COMMAND", "ssh -v")

        start = time.perf_counter()
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        out, err = proc.communicate()
        duration = time.perf_counter() - start
        rc = proc.returncode

        self._write_log(cmd, env, duration, rc, out or "", err or "")
        self._attach_log_to_allure()

        return GitResult(code=rc, stdout=(out or "").strip(), stderr=(err or "").strip(), duration=duration)

    # -----------------------
    # Core operations
    # -----------------------

    def init(self) -> GitResult:
        return self._run(["init"])

    def clone(self, target_dir: Optional[str] = None, repo_url: Optional[str] = None,
              protocol: Optional[str] = None, host: Optional[str] = None,
              owner: Optional[str] = None, repo: Optional[str] = None) -> GitResult:
        url = repo_url or self._make_repo_url(protocol=protocol, host=host, owner=owner, repo=repo)
        args = ["clone", url]
        if target_dir:
            args.append(target_dir)
        return self._run(args)

    def add(self, path: str = ".") -> GitResult:
        return self._run(["add", path])

    def commit(self, message: str) -> GitResult:
        return self._run(["commit", "-m", message])

    def push(self, remote: str = "origin", branch: str = "main") -> GitResult:
        return self._run(["push", remote, branch])

    def pull(self, remote: str = "origin", branch: str = "main") -> GitResult:
        return self._run(["pull", remote, branch])

    def fetch(self, remote: str = "origin") -> GitResult:
        return self._run(["fetch", remote])

    def status(self) -> GitResult:
        return self._run(["status"])

    def checkout(self, branch: str) -> GitResult:
        return self._run(["checkout", branch])

    def branch(self, name: str) -> GitResult:
        return self._run(["branch", name])

    def merge(self, branch: str) -> GitResult:
        return self._run(["merge", branch])

    def rebase(self, branch: str) -> GitResult:
        return self._run(["rebase", branch])

    def tag(self, name: str, message: Optional[str] = None) -> GitResult:
        args = ["tag"]
        if message:
            args.extend(["-a", name, "-m", message])
        else:
            args.append(name)
        return self._run(args)

    def list_tags(self) -> GitResult:
        return self._run(["tag", "--list"])

    def delete_tag(self, name: str) -> GitResult:
        return self._run(["tag", "-d", name])

    def remote_add(self, name: str, url: str) -> GitResult:
        return self._run(["remote", "add", name, url])

    def remote_remove(self, name: str) -> GitResult:
        return self._run(["remote", "remove", name])

    def remote_list(self) -> GitResult:
        return self._run(["remote", "-v"])

    def config_set(self, key: str, value: str) -> GitResult:
        return self._run(["config", key, value])

    def config_get(self, key: str) -> GitResult:
        return self._run(["config", "--get", key])

    def log(self, n: int = 10) -> GitResult:
        return self._run(["log", f"-n{n}", "--oneline"])

    def diff(self, rev1: str = "HEAD~1", rev2: str = "HEAD") -> GitResult:
        return self._run(["diff", f"{rev1}..{rev2}"])

    def reset(self, mode: str = "soft", commit: str = "HEAD~1") -> GitResult:
        return self._run(["reset", f"--{mode}", commit])

    def stash_save(self, message: str = "") -> GitResult:
        args = ["stash", "save"]
        if message:
            args.append(message)
        return self._run(args)

    def stash_pop(self, index: int = 0) -> GitResult:
        return self._run(["stash", "pop", f"stash@{{{index}}}"])

    def stash_list(self) -> GitResult:
        return self._run(["stash", "list"])

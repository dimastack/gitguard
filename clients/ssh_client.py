from __future__ import annotations

import subprocess
import logging
import datetime
import shlex
from pathlib import Path
from typing import Optional, List

try:
    import allure
    _HAS_ALLURE = True
except Exception:
    _HAS_ALLURE = False

logger = logging.getLogger("gitguard")


class SSHResult:
    """Result of an SSH command."""
    def __init__(self, code: int, stdout: str, stderr: str, duration: float):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration

    def ok(self) -> bool:
        return self.code == 0


class SSHClient:
    """
    Simple SSH client wrapper for executing commands on a remote host.
    Uses system `ssh` binary (not paramiko).
    Logs results and optionally attaches to Allure.
    """

    def __init__(
        self,
        host: str,
        user: str = "git",
        port: int = 22,
        key_path: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        attach_logs_always: bool = True,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = Path(key_path) if key_path else None
        self.attach_logs_always = attach_logs_always

        # artifacts dir
        if artifacts_dir:
            self.artifacts = Path(artifacts_dir)
        else:
            self.artifacts = Path.cwd() / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.artifacts / f"ssh-client-{ts}.log"

    def _build_ssh_command(self, remote_cmd: str) -> List[str]:
        cmd = ["ssh", "-p", str(self.port), "-o", "StrictHostKeyChecking=no"]
        if self.key_path:
            cmd += ["-i", str(self.key_path)]
        cmd.append(f"{self.user}@{self.host}")
        cmd.append(remote_cmd)
        return cmd

    def _write_log(self, cmd: List[str], rc: int, out: str, err: str, duration: float) -> None:
        header = (
            f"\n---\nTime: {datetime.datetime.utcnow().isoformat()}Z\n"
            f"Command: {shlex.join(cmd)}\n"
            f"Return code: {rc}\n"
            f"Duration: {duration:.6f} sec\n"
            f"---\n"
        )
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(header)
            if out:
                f.write("STDOUT:\n" + out + "\n")
            if err:
                f.write("STDERR:\n" + err + "\n")

    def _attach_log_to_allure(self) -> None:
        if not (self.attach_logs_always and _HAS_ALLURE):
            return
        try:
            with open(self.log_path, "rb") as fh:
                allure.attach(fh.read(), name="ssh-client-log", attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            logger.exception("Failed to attach SSH log: %s", e)

    def run(self, remote_cmd: str, check: bool = True) -> SSHResult:
        cmd = self._build_ssh_command(remote_cmd)
        logger.debug("Running SSH command: %s", shlex.join(cmd))

        start = datetime.datetime.utcnow()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        duration = (datetime.datetime.utcnow() - start).total_seconds()
        rc = proc.returncode

        # logging
        try:
            self._write_log(cmd, rc, out or "", err or "", duration)
            self._attach_log_to_allure()
        except Exception:
            logger.exception("SSH logging failed")

        result = SSHResult(code=rc, stdout=(out or "").strip(), stderr=(err or "").strip(), duration=duration)

        if check and not result.ok():
            raise RuntimeError(f"SSH command failed: {rc}\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        return result

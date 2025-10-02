from __future__ import annotations

import logging
import os

from typing import Any, Dict, Optional

from gitguard.clients.http_client import HttpClient, HttpResult

logger = logging.getLogger("gitguard")


class GiteaHttpClient(HttpClient):
    """
    Specialized HTTP client for interacting with Gitea REST API.
    Extends the base HttpClient with convenience methods for common API calls.
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: int = 10,
        attach_to_allure: bool = True,
    ):
        api_url = base_url.rstrip("/") + "/api/v1"

        # Try to resolve token automatically
        resolved_token = (
            token
            or os.getenv("GITEA_ADMIN_TOKEN")
            or self._load_token_file()
        )

        if not resolved_token:
            logger.warning("No Gitea token found (GITEA_ADMIN_TOKEN or /data/gitea_admin_token). API calls may fail.")

        super().__init__(base_url=api_url, timeout=timeout, attach_to_allure=attach_to_allure)
        self.token = resolved_token

    def _auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    @staticmethod
    def _load_token_file(path: str = "/data/gitea_admin_token") -> Optional[str]:
        """Try to read token from mounted file (used in Docker setup)."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read token file {path}: {e}")
        return None

    # ---------- Health ----------

    def health_check(self) -> HttpResult:
        """Check if Gitea API is reachable."""
        return self.get("", headers=self._auth_headers())

    def version(self) -> HttpResult:
        """Get Gitea version info."""
        return self.get("version", headers=self._auth_headers())

    # ---------- Users ----------

    def get_user(self, username: str) -> HttpResult:
        return self.get(f"users/{username}", headers=self._auth_headers())

    # ---------- Orgs ----------

    def list_orgs(self) -> HttpResult:
        return self.get("user/orgs", headers=self._auth_headers())

    def create_org(self, org_name: str, description: str = "") -> HttpResult:
        payload = {"full_name": org_name, "description": description}
        return self.post("orgs", json=payload, headers=self._auth_headers())

    # ---------- Repositories ----------

    def list_repos(self, username: Optional[str] = None) -> HttpResult:
        path = f"users/{username}/repos" if username else "user/repos"
        return self.get(path, headers=self._auth_headers())

    def create_repo(self, name: str, private: bool = False, description: str = "") -> HttpResult:
        payload = {"name": name, "private": private, "description": description}
        return self.post("user/repos", json=payload, headers=self._auth_headers())

    def get_repo(self, owner: str, repo: str) -> HttpResult:
        return self.get(f"repos/{owner}/{repo}", headers=self._auth_headers())

    def delete_repo(self, owner: str, repo: str) -> HttpResult:
        return self.delete(f"repos/{owner}/{repo}", headers=self._auth_headers())

    def rename_repo(self, owner: str, repo: str, new_name: str) -> HttpResult:
        payload = {"name": new_name}
        return self.patch(f"repos/{owner}/{repo}", json=payload, headers=self._auth_headers())

    # ---------- Admin: Users ----------

    def list_users(self) -> HttpResult:
        return self.get("admin/users", headers=self._auth_headers())

    def create_user(self, username: str, email: str, password: str, must_change_password: bool = False) -> HttpResult:
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "must_change_password": must_change_password,
        }
        return self.post("admin/users", json=payload, headers=self._auth_headers())

    def delete_user(self, username: str) -> HttpResult:
        return self.delete(f"admin/users/{username}", headers=self._auth_headers())

    def edit_user(self, username: str, **kwargs: Any) -> HttpResult:
        return self.patch(f"admin/users/{username}", json=kwargs, headers=self._auth_headers())
    
    # ---------- Admin: Orgs ----------

    def admin_create_org(self, owner_username: str, org_name: str, description: str = "") -> HttpResult:
        payload = {"username": owner_username, "full_name": org_name, "description": description}
        return self.post(f"admin/users/{owner_username}/orgs", json=payload, headers=self._auth_headers())

    # ---------- Admin: Repositories ----------

    def admin_create_repo(self, username: str, repo_name: str, private: bool = False) -> HttpResult:
        payload = {"name": repo_name, "private": private}
        return self.post(f"admin/users/{username}/repos", json=payload, headers=self._auth_headers())

    # ---------- Admin: Misc ----------

    def list_unadopted_repos(self) -> HttpResult:
        return self.get("admin/unadopted", headers=self._auth_headers())

    def adopt_unadopted_repo(self, owner: str, repo_name: str) -> HttpResult:
        payload = {"repo_name": repo_name, "owner": owner}
        return self.post("admin/unadopted", json=payload, headers=self._auth_headers())

    def delete_unadopted_repo(self, owner: str, repo_name: str) -> HttpResult:
        return self.delete(f"admin/unadopted/{owner}/{repo_name}", headers=self._auth_headers())

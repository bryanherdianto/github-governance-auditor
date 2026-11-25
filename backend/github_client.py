import base64
import re
from typing import Any
from urllib.parse import urlparse
import httpx

OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
PRIORITY_NAMES = ("readme", "license", "model", "card", "security", "contributing", "notice")


def parse_github_url(url: str) -> tuple[str, str]:
    # Extract and validate (owner, repo) from a GitHub URL or owner/repo shorthand.
    raw = (url or "").strip()
    if not raw:
        raise ValueError("Repository URL cannot be empty.")

    if "://" not in raw and not raw.startswith("github.com"):
        parts = [p for p in raw.strip("/").split("/") if p]
    else:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("URL must point to github.com.")
        parts = [p for p in parsed.path.strip("/").split("/") if p]

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository format. Expected https://github.com/<owner>/<repo>.")

    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not (OWNER_REPO_RE.match(owner) and OWNER_REPO_RE.match(repo)):
        raise ValueError("Invalid GitHub owner or repository name.")
    return owner, repo


class GitHubClient:
    # Thin GitHub REST API wrapper with safe error and rate-limit handling.

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-compliance-agent",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers=headers,
            timeout=timeout,
            transport=transport,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str) -> tuple[Any | None, str | None]:
        # Execute a GET request and return (json_data, error_message).
        try:
            resp = self._client.get(path)
        except httpx.TimeoutException:
            return None, f"GitHub API request timed out for {path}."
        except httpx.RequestError as exc:
            return None, f"GitHub API network error: {exc}"

        if resp.status_code == 404:
            return None, f"Not found (404): {path}"
        if resp.status_code in (403, 429):
            if resp.headers.get("X-RateLimit-Remaining") == "0" or resp.status_code == 429:
                return None, "GitHub API rate limit exceeded. Configure GITHUB_TOKEN for higher limits."
            return None, f"GitHub API access forbidden ({resp.status_code}) for {path}."
        if resp.status_code >= 500:
            return None, f"GitHub API server error ({resp.status_code}) for {path}."
        if resp.status_code >= 400:
            return None, f"GitHub API error ({resp.status_code}) for {path}."

        try:
            return resp.json(), None
        except ValueError:
            return None, f"Unexpected non-JSON response from GitHub API for {path}."

    def get_repo_metadata(self, owner: str, repo: str) -> dict[str, Any]:
        # Retrieve repository metadata including default branch and detected license.
        data, err = self._get(f"/repos/{owner}/{repo}")
        url = f"https://github.com/{owner}/{repo}"
        if err or not isinstance(data, dict):
            return {"ok": False, "source_url": url, "data": None, "error": err or "Unexpected metadata payload."}

        lic = data.get("license") or {}
        return {
            "ok": True,
            "source_url": data.get("html_url", url),
            "data": {
                "full_name": data.get("full_name", f"{owner}/{repo}"),
                "description": data.get("description"),
                "default_branch": data.get("default_branch", "main"),
                "visibility": data.get("visibility", "public"),
                "license": {
                    "spdx_id": lic.get("spdx_id"),
                    "name": lic.get("name"),
                    "key": lic.get("key"),
                }
                if lic
                else None,
            },
            "error": None,
        }

    def list_repo_files(self, owner: str, repo: str, branch: str = "main", limit: int = 250) -> dict[str, Any]:
        # List repository file paths via recursive tree with /contents fallback.
        tree_url = f"https://github.com/{owner}/{repo}/tree/{branch}"
        data, err = self._get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")

        if isinstance(data, dict) and isinstance(data.get("tree"), list):
            files = [item["path"] for item in data["tree"] if item.get("type") == "blob" and item.get("path")]
            # Keep governance and top-level docs first when capping large repositories.
            prioritized = sorted(
                files,
                key=lambda p: (0 if any(k in p.lower() for k in PRIORITY_NAMES) else 1, p.count("/"), p.lower()),
            )
            return {
                "ok": True,
                "source_url": tree_url,
                "data": {"files": prioritized[:limit], "total_files": len(files), "truncated": bool(data.get("truncated")) or len(files) > limit},
                "error": None,
            }

        # Fall back to targeted directory listing when git tree is unavailable.
        collected: list[str] = []
        last_err = err
        for subdir in ("", ".github", "docs"):
            suffix = f"/{subdir}" if subdir else ""
            entries, sub_err = self._get(f"/repos/{owner}/{repo}/contents{suffix}")
            if isinstance(entries, list):
                collected.extend(e["path"] for e in entries if e.get("path"))
            elif not subdir and sub_err:
                last_err = sub_err

        if collected:
            return {"ok": True, "source_url": tree_url, "data": {"files": collected[:limit], "total_files": len(collected), "truncated": False}, "error": None}
        return {"ok": False, "source_url": tree_url, "data": None, "error": last_err or "Unable to list repository files."}

    def read_repo_file(self, owner: str, repo: str, path: str, max_chars: int = 12000) -> dict[str, Any]:
        # Read and UTF-8 decode a repository file, truncating safely at max_chars.
        clean_path = path.lstrip("/")
        fallback_url = f"https://github.com/{owner}/{repo}/blob/main/{clean_path}"
        data, err = self._get(f"/repos/{owner}/{repo}/contents/{clean_path}")
        if err or not isinstance(data, dict):
            return {"ok": False, "source_url": fallback_url, "data": None, "error": err or "Unexpected file payload."}

        html_url = data.get("html_url", fallback_url)
        if data.get("type") != "file":
            return {"ok": False, "source_url": html_url, "data": None, "error": f"Path '{clean_path}' is not a file."}

        raw_content = data.get("content", "")
        encoding = data.get("encoding")
        if encoding != "base64" or not isinstance(raw_content, str):
            return {"ok": False, "source_url": html_url, "data": None, "error": f"Unsupported encoding '{encoding}' for '{clean_path}'."}

        try:
            text = base64.b64decode(raw_content).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return {"ok": False, "source_url": html_url, "data": None, "error": f"File '{clean_path}' is binary or not valid UTF-8."}

        truncated = len(text) > max_chars
        return {
            "ok": True,
            "source_url": html_url,
            "data": {"path": clean_path, "size": data.get("size", len(text)), "truncated": truncated, "content": text[:max_chars]},
            "error": None,
        }

    def check_org_security_policy(self, owner: str) -> dict[str, Any]:
        # Check whether the GitHub owner defines an organization-level SECURITY.md.
        candidates = ("SECURITY.md", ".github/SECURITY.md")
        last_err: str | None = None
        for rel_path in candidates:
            res = self.read_repo_file(owner, ".github", rel_path)
            if res["ok"]:
                return {"ok": True, "source_url": res["source_url"], "data": {"found": True, **res["data"]}, "error": None}
            last_err = res["error"]
            if last_err and "rate limit" in last_err.lower():
                return {"ok": False, "source_url": f"https://github.com/{owner}/.github", "data": None, "error": last_err}

        return {
            "ok": True,
            "source_url": f"https://github.com/{owner}/.github",
            "data": {"found": False, "checked_paths": list(candidates)},
            "error": None,
        }

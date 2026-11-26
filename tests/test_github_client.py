import base64
import httpx
import pytest

from backend.github_client import GitHubClient, parse_github_url


def test_parse_github_url_variants():
    assert parse_github_url("https://github.com/openai/whisper") == ("openai", "whisper")
    assert parse_github_url("https://github.com/openai/whisper.git") == ("openai", "whisper")
    assert parse_github_url("https://github.com/openai/whisper/tree/main") == ("openai", "whisper")
    assert parse_github_url("openai/whisper") == ("openai", "whisper")


@pytest.mark.parametrize("bad_url", ["", "https://gitlab.com/a/b", "https://github.com/onlyowner", "not a url"])
def test_parse_github_url_invalid(bad_url: str):
    with pytest.raises(ValueError):
        parse_github_url(bad_url)


def test_github_client_metadata_tree_and_file():
    encoded = base64.b64encode(b"# Whisper\nSpeech recognition model.\n").decode("ascii")

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/openai/whisper":
            return httpx.Response(200, json={"full_name": "openai/whisper", "default_branch": "main", "html_url": "https://github.com/openai/whisper", "license": {"spdx_id": "MIT", "name": "MIT License", "key": "mit"}})
        if path == "/repos/openai/whisper/git/trees/main":
            return httpx.Response(200, json={"tree": [{"path": "README.md", "type": "blob"}, {"path": "whisper/model.py", "type": "blob"}], "truncated": False})
        if path == "/repos/openai/whisper/contents/README.md":
            return httpx.Response(200, json={"type": "file", "encoding": "base64", "content": encoded, "size": 35, "html_url": "https://github.com/openai/whisper/blob/main/README.md"})
        return httpx.Response(404, json={"message": "Not Found"})

    client = GitHubClient(transport=httpx.MockTransport(handler))
    meta = client.get_repo_metadata("openai", "whisper")
    assert meta["ok"] is True
    assert meta["data"]["license"]["spdx_id"] == "MIT"

    files = client.list_repo_files("openai", "whisper", "main")
    assert files["ok"] is True
    assert files["data"]["files"][0] == "README.md"

    readme = client.read_repo_file("openai", "whisper", "README.md", max_chars=15)
    assert readme["ok"] is True
    assert readme["data"]["truncated"] is True
    assert readme["data"]["content"] == "# Whisper\nSpeec"
    client.close()


def test_github_client_tree_fallback_and_errors():
    bad_b64 = base64.b64encode(b"\xff\xfe\x00").decode("ascii")

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.startswith("/repos/org/repo/git/trees"):
            return httpx.Response(404)
        if path == "/repos/org/repo/contents":
            return httpx.Response(200, json=[{"path": "README.md"}])
        if path == "/repos/org/repo/contents/.github":
            return httpx.Response(404)
        if path == "/repos/org/repo/contents/docs":
            return httpx.Response(404)
        if path == "/repos/org/repo/contents/bin.dat":
            return httpx.Response(200, json={"type": "file", "encoding": "base64", "content": bad_b64})
        if path == "/repos/org/repo/contents/limited":
            return httpx.Response(403, headers={"X-RateLimit-Remaining": "0"})
        return httpx.Response(404)

    client = GitHubClient(transport=httpx.MockTransport(handler))
    listed = client.list_repo_files("org", "repo", "main")
    assert listed["ok"] is True
    assert "README.md" in listed["data"]["files"]

    binary_res = client.read_repo_file("org", "repo", "bin.dat")
    assert binary_res["ok"] is False
    assert "binary" in binary_res["error"].lower()

    rate_res = client.read_repo_file("org", "repo", "limited")
    assert rate_res["ok"] is False
    assert "rate limit" in rate_res["error"].lower()
    client.close()


def test_github_client_timeout_and_org_security():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/repos/acme/.github/contents/SECURITY.md":
            raise httpx.ReadTimeout("timed out")
        return httpx.Response(404)

    client = GitHubClient(transport=httpx.MockTransport(handler))
    meta = client.get_repo_metadata("acme", "app")
    assert meta["ok"] is False
    assert "404" in meta["error"]

    org_sec = client.check_org_security_policy("acme")
    assert org_sec["ok"] is True
    assert org_sec["data"]["found"] is False
    client.close()

"""API endpoint tests for Shortly."""
import json
import pytest


def post_shorten(client, long_url, **kwargs):
    payload = {"long_url": long_url, **kwargs}
    return client.post(
        "/api/shorten",
        data=json.dumps(payload),
        content_type="application/json",
    )


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code in (200, 503)
        data = r.get_json()
        assert "status" in data
        assert "database" in data


class TestShorten:
    def test_shorten_valid_url(self, client):
        r = post_shorten(client, "https://example.com/some/long/path")
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert "short_url" in data
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")

    def test_shorten_auto_prepend_https(self, client):
        r = post_shorten(client, "example.com")
        assert r.status_code == 201
        # Should have normalised to https://example.com

    def test_shorten_missing_url(self, client):
        r = client.post("/api/shorten",
                        data=json.dumps({}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_shorten_invalid_url(self, client):
        r = post_shorten(client, "not-a-url-at-all!!!")
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_shorten_invalid_scheme(self, client):
        r = post_shorten(client, "ftp://example.com")
        assert r.status_code == 400

    def test_shorten_custom_alias(self, client):
        r = post_shorten(client, "https://example.com", custom_alias="myalias")
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert "myalias" in data["short_url"]

    def test_shorten_duplicate_alias(self, client):
        post_shorten(client, "https://example.com", custom_alias="dupe")
        r = post_shorten(client, "https://other.com", custom_alias="dupe")
        assert r.status_code == 409

    def test_shorten_alias_too_short(self, client):
        r = post_shorten(client, "https://example.com", custom_alias="ab")
        assert r.status_code == 400

    def test_shorten_alias_invalid_chars(self, client):
        r = post_shorten(client, "https://example.com", custom_alias="bad alias!")
        assert r.status_code == 400

    def test_shorten_reserved_alias(self, client):
        r = post_shorten(client, "https://example.com", custom_alias="api")
        assert r.status_code == 400

    def test_shorten_with_ttl(self, client):
        r = post_shorten(client, "https://example.com", ttl_days=7)
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert data["expires_at"] is not None

    def test_shorten_invalid_ttl(self, client):
        r = post_shorten(client, "https://example.com", ttl_days=999)
        assert r.status_code == 400

    def test_shorten_non_json_body(self, client):
        r = client.post("/api/shorten",
                        data="not json",
                        content_type="text/plain")
        assert r.status_code == 400


class TestRedirect:
    def test_redirect_works(self, client):
        r = post_shorten(client, "https://example.com")
        short_code = r.get_json()["data"]["short_url"].split("/")[-1]

        r2 = client.get(f"/{short_code}", follow_redirects=False)
        assert r2.status_code == 302
        assert r2.headers["Location"] == "https://example.com"

    def test_redirect_increments_clicks(self, client):
        r = post_shorten(client, "https://example.com")
        short_code = r.get_json()["data"]["short_url"].split("/")[-1]

        client.get(f"/{short_code}")
        client.get(f"/{short_code}")

        r3 = client.get(f"/api/analytics/{short_code}")
        assert r3.get_json()["data"]["clicks"] == 2

    def test_redirect_not_found(self, client):
        r = client.get("/nonexistent-code", follow_redirects=False)
        assert r.status_code == 404


class TestAnalytics:
    def test_analytics_api(self, client):
        r = post_shorten(client, "https://example.com")
        short_code = r.get_json()["data"]["short_url"].split("/")[-1]

        r2 = client.get(f"/api/analytics/{short_code}")
        assert r2.status_code == 200
        data = r2.get_json()["data"]
        assert data["clicks"] == 0
        assert data["short_code"] == short_code
        assert "chart_data" in data
        assert len(data["chart_data"]) == 14

    def test_analytics_not_found(self, client):
        r = client.get("/api/analytics/doesnotexist")
        assert r.status_code == 404

    def test_analytics_page(self, client):
        r = post_shorten(client, "https://example.com")
        short_code = r.get_json()["data"]["short_url"].split("/")[-1]

        r2 = client.get(f"/analytics/{short_code}")
        assert r2.status_code == 200
        assert b"short_code" in r2.data or short_code.encode() in r2.data


class TestPages:
    def test_index_page(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"Shortly" in r.data

    def test_404_page(self, client):
        r = client.get("/definitely/does/not/exist")
        assert r.status_code == 404

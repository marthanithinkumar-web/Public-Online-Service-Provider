from pathlib import Path

from app.ai_tools import posp_operations


def _seo_root(tmp_path, monkeypatch):
    source = tmp_path / "backend" / "app" / "ai_tools" / "posp_operations.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.touch()
    public = tmp_path / "frontend" / "public"
    public.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(posp_operations, "__file__", str(source))
    return public


def test_seo_health_accepts_crawlable_robots_and_valid_sitemap(tmp_path, monkeypatch):
    public = _seo_root(tmp_path, monkeypatch)
    (public / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: https://pospindia.onrender.com/sitemap.xml\n",
        encoding="utf-8",
    )
    (public / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://pospindia.onrender.com/</loc></url>'
        '<url><loc>https://pospindia.onrender.com/jobs</loc></url>'
        '</urlset>',
        encoding="utf-8",
    )

    result = posp_operations.seo_health({})

    assert result["healthy"] is True
    assert result["issues"] == []
    assert result["robots_allows_root"] is True
    assert result["robots_has_sitemap"] is True
    assert result["sitemap_is_xml"] is True
    assert result["sitemap_url_count"] == 2


def test_seo_health_reports_missing_files_as_issues_not_healthy(tmp_path, monkeypatch):
    _seo_root(tmp_path, monkeypatch)

    result = posp_operations.seo_health({})

    assert result["healthy"] is False
    assert "robots_missing" in result["issues"]
    assert "sitemap_missing" in result["issues"]
    assert "robots_sitemap_missing" in result["issues"]
    assert result["sitemap_url_count"] == 0


def test_seo_health_detects_explicit_root_block_and_malformed_sitemap(tmp_path, monkeypatch):
    public = _seo_root(tmp_path, monkeypatch)
    (public / "robots.txt").write_text(
        "User-agent: *\nDisallow: /\nSitemap: https://pospindia.onrender.com/sitemap.xml\n",
        encoding="utf-8",
    )
    (public / "sitemap.xml").write_text("<not-a-sitemap>", encoding="utf-8")

    result = posp_operations.seo_health({})

    assert result["healthy"] is False
    assert result["robots_root_blocked"] is True
    assert "robots_root_blocked" in result["issues"]
    assert "sitemap_invalid" in result["issues"]

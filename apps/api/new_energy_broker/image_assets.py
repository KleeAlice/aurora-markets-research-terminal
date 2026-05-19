from __future__ import annotations

import html
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .schemas import ImageAsset, NewsCard

ASSET_ROOT = Path(__file__).resolve().parents[2] / "runtime_assets" / "images"
ASSET_ROOT.mkdir(parents=True, exist_ok=True)
CACHE_TTL_SECONDS = 6 * 60 * 60
MAX_IMAGE_BYTES = 4_000_000

IMAGE_PAGES = {
    "byd": "https://www.bydglobal.com/en/news.html",
    "battery": "https://www.catl.com/en/news/",
    "tesla": "https://www.tesla.com/blog",
    "ev": "https://www.iea.org/energy-system/transport/electric-vehicles",
}

COMMONS_IMAGE_QUERIES = {
    "byd": "BYD Seal electric vehicle",
    "battery": "CATL battery electric vehicle",
    "tesla": "Tesla electric vehicle",
    "ev": "electric vehicle charging station",
}


def _offline_image_mode() -> bool:
    return os.environ.get("AURORA_IMAGE_FETCH_MODE", "").strip().lower() in {"fallback", "offline", "disabled"}


def _asset_id(news: NewsCard, index: int) -> str:
    digest = hashlib.sha1(f"{news.title}|{news.source}|{index}".encode("utf-8")).hexdigest()[:12]
    key = re.sub(r"[^a-z0-9]+", "-", (news.image_key or "ev").lower()).strip("-") or "ev"
    return f"{key}-{digest}"


def _meta_path(asset_id: str) -> Path:
    return ASSET_ROOT / f"{asset_id}.json"


def _request(url: str, timeout: float = 4.0, max_bytes: int = 2_500_000) -> tuple[bytes, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AuroraMarketsResearchAgent/0.1 (+research-only)",
            "Accept": "text/html,image/avif,image/webp,image/png,image/jpeg,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type() or "application/octet-stream"
        return response.read(max_bytes), response.geturl(), content_type


def _absolute_url(value: str, source_url: str) -> str | None:
    value = html.unescape(value.strip())
    if not value or value.startswith("data:"):
        return None
    return urllib.parse.urljoin(source_url, value)


def _looks_like_image(url: str) -> bool:
    return bool(re.search(r"\.(avif|webp|png|jpe?g)(\?|$)", url, flags=re.IGNORECASE))


def _extract_image_url(source_url: str) -> str | None:
    try:
        raw, final_url, _ = _request(source_url)
        text = raw.decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _absolute_url(match.group(1), final_url)
    img_matches = re.findall(r"<img\b[^>]+(?:src|data-src|data-original)=['\"]([^'\"]+)['\"][^>]*>", text, flags=re.IGNORECASE)
    for candidate in img_matches[:30]:
        image_url = _absolute_url(candidate, final_url)
        if image_url and _looks_like_image(image_url):
            return image_url
    return None


def _search_source_page(news: NewsCard) -> str | None:
    if news.source_url:
        return news.source_url
    query = f"{news.title} {news.source}".strip()
    search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        raw, _, _ = _request(search_url, timeout=5.0)
    except (urllib.error.URLError, TimeoutError, OSError):
        return IMAGE_PAGES.get(news.image_key or "ev", IMAGE_PAGES["ev"])
    text = raw.decode("utf-8", errors="ignore")
    links = re.findall(r'class=["\']result__a["\'][^>]+href=["\']([^"\']+)["\']', text, flags=re.IGNORECASE)
    for link in links[:6]:
        href = html.unescape(link)
        if "uddg=" in href:
            parsed = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed.query)
            href = params.get("uddg", [href])[0]
        if href.startswith("http") and not any(blocked in href for blocked in ("duckduckgo.com", "bing.com/search", "google.com/search")):
            return href
    return IMAGE_PAGES.get(news.image_key or "ev", IMAGE_PAGES["ev"])


def _search_commons_image(news: NewsCard) -> str | None:
    query = COMMONS_IMAGE_QUERIES.get(news.image_key or "ev") or news.title
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "6",
        "gsrlimit": "5",
        "gsrsearch": query,
        "prop": "imageinfo",
        "iiprop": "url|mime",
    }
    url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    try:
        raw, _, _ = _request(url, timeout=5.0)
        payload = json.loads(raw.decode("utf-8", errors="ignore"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        image_url = info.get("url")
        mime = info.get("mime", "")
        if image_url and mime.startswith("image/") and not image_url.lower().endswith(".svg"):
            return image_url
    return None


def _suffix_for(content_type: str, url: str) -> tuple[str, str]:
    content_type = (content_type or "").split(";")[0].lower()
    mapping = {
        "image/jpeg": (".jpg", "image/jpeg"),
        "image/jpg": (".jpg", "image/jpeg"),
        "image/png": (".png", "image/png"),
        "image/webp": (".webp", "image/webp"),
        "image/avif": (".avif", "image/avif"),
        "image/svg+xml": (".svg", "image/svg+xml"),
    }
    if content_type in mapping:
        return mapping[content_type]
    match = re.search(r"\.(avif|webp|png|jpe?g|svg)(\?|$)", url, flags=re.IGNORECASE)
    if match:
        ext = match.group(1).lower()
        if ext in {"jpg", "jpeg"}:
            return ".jpg", "image/jpeg"
        if ext == "svg":
            return ".svg", "image/svg+xml"
        return f".{ext}", f"image/{ext}"
    return ".jpg", "image/jpeg"


def _load_cached_asset(asset_id: str, title: str) -> ImageAsset | None:
    meta_path = _meta_path(asset_id)
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - float(meta.get("created_at", 0)) > CACHE_TTL_SECONDS:
        return None
    if meta.get("status") != "downloaded":
        return None
    if not (ASSET_ROOT / f"{asset_id}{meta.get('suffix', '')}").exists():
        return None
    return ImageAsset(
        id=asset_id,
        title=title,
        source_url=meta["source_url"],
        image_url=meta.get("image_url"),
        local_url=f"/api/assets/images/{asset_id}",
        attribution=meta["attribution"],
        width=None,
        height=None,
        status=meta.get("status", "downloaded"),
    )


def _write_meta(asset_id: str, payload: dict[str, object]) -> None:
    _meta_path(asset_id).write_text(json.dumps({"created_at": time.time(), **payload}, ensure_ascii=False), encoding="utf-8")


def _fallback_svg(asset_id: str, title: str, key: str) -> str:
    colors = {
        "byd": ("#e5394a", "#edf5ff"),
        "tesla": ("#242b3a", "#f2f6ff"),
        "battery": ("#18a66a", "#edf8f2"),
        "ev": ("#0d63ff", "#f2f7ff"),
    }
    accent, bg = colors.get(key, colors["ev"])
    safe_title = html.escape(title[:80])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420" viewBox="0 0 720 420">
  <rect width="720" height="420" rx="28" fill="{bg}"/>
  <path d="M70 298 C160 230 230 240 320 160 S520 90 650 132" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
  <circle cx="170" cy="286" r="34" fill="white" stroke="{accent}" stroke-width="14"/>
  <circle cx="535" cy="160" r="34" fill="white" stroke="{accent}" stroke-width="14"/>
  <rect x="64" y="56" width="168" height="40" rx="20" fill="{accent}" opacity=".14"/>
  <text x="88" y="83" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="20" font-weight="700" fill="{accent}">Aurora Source Image</text>
  <text x="64" y="360" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="26" font-weight="800" fill="#17213d">{safe_title}</text>
</svg>"""
    path = ASSET_ROOT / f"{asset_id}.svg"
    path.write_text(svg, encoding="utf-8")
    return f"/api/assets/images/{asset_id}"


def build_news_image_asset(news: NewsCard, index: int) -> ImageAsset:
    key = news.image_key or "ev"
    asset_id = _asset_id(news, index)
    cached = _load_cached_asset(asset_id, news.title)
    if cached:
        return cached

    if _offline_image_mode():
        source_url = news.source_url or IMAGE_PAGES.get(key, IMAGE_PAGES["ev"])
        fallback_url = _fallback_svg(asset_id, news.title, key)
        attribution = f"Fallback visual derived from Aurora data; source checked: {source_url}"
        _write_meta(
            asset_id,
            {
                "source_url": source_url,
                "image_url": None,
                "suffix": ".svg",
                "media_type": "image/svg+xml",
                "attribution": attribution,
                "status": "fallback",
            },
        )
        return ImageAsset(
            id=asset_id,
            title=news.title,
            source_url=source_url,
            image_url=None,
            local_url=fallback_url,
            attribution=attribution,
            status="fallback",
        )

    source_url = _search_source_page(news) or IMAGE_PAGES.get(key, IMAGE_PAGES["ev"])
    image_url = _extract_image_url(source_url) or _search_commons_image(news)
    if image_url:
        try:
            content, final_image_url, content_type = _request(image_url, max_bytes=MAX_IMAGE_BYTES)
            suffix, media_type = _suffix_for(content_type, final_image_url)
            local_path = ASSET_ROOT / f"{asset_id}{suffix}"
            local_path.write_bytes(content)
            attribution = f"{news.source} / {source_url}"
            _write_meta(
                asset_id,
                {
                    "source_url": source_url,
                    "image_url": final_image_url,
                    "suffix": suffix,
                    "media_type": media_type,
                    "attribution": attribution,
                    "status": "downloaded",
                },
            )
            return ImageAsset(
                id=asset_id,
                title=news.title,
                source_url=source_url,
                image_url=final_image_url,
                local_url=f"/api/assets/images/{asset_id}",
                attribution=attribution,
                status="downloaded",
            )
        except (urllib.error.URLError, TimeoutError, OSError):
            attribution = f"{news.source} / {source_url}"
            return ImageAsset(
                id=asset_id,
                title=news.title,
                source_url=source_url,
                image_url=image_url,
                local_url=image_url,
                attribution=attribution,
                status="remote",
            )
    fallback_url = _fallback_svg(asset_id, news.title, key)
    attribution = f"Fallback visual derived from Aurora data; source checked: {source_url}"
    _write_meta(
        asset_id,
        {
            "source_url": source_url,
            "image_url": image_url,
            "suffix": ".svg",
            "media_type": "image/svg+xml",
            "attribution": attribution,
            "status": "fallback",
        },
    )
    return ImageAsset(
        id=asset_id,
        title=news.title,
        source_url=source_url,
        image_url=image_url,
        local_url=fallback_url,
        attribution=attribution,
        status="fallback",
    )


def image_bytes(asset_id: str) -> tuple[bytes, str]:
    for suffix, media_type in [(".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp"), (".avif", "image/avif"), (".svg", "image/svg+xml")]:
        path = ASSET_ROOT / f"{asset_id}{suffix}"
        if path.exists():
            return path.read_bytes(), media_type
    raise FileNotFoundError(asset_id)

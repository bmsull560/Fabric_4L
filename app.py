import re
import xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; SimpleSitemapTool/1.0; +https://example.com)"
TIMEOUT = 15


def normalize_site_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def canonicalize_url(url: str, strip_query: bool = True) -> str:
    parsed = urlparse(url)
    query = "" if strip_query else parsed.query
    cleaned = parsed._replace(fragment="", query=query)
    url = urlunparse(cleaned)
    if url.endswith("/") and parsed.path not in ("", "/"):
        url = url[:-1]
    return url


def same_site(url: str, site_root: str) -> bool:
    a = urlparse(url).netloc.lower().replace("www.", "")
    b = urlparse(site_root).netloc.lower().replace("www.", "")
    return a == b


def fetch(url: str):
    return requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)


def discover_sitemaps(site_root: str) -> list[str]:
    found = []

    robots_url = urljoin(site_root, "/robots.txt")
    try:
        r = fetch(robots_url)
        if r.ok:
            for line in r.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sm = line.split(":", 1)[1].strip()
                    if sm:
                        found.append(sm)
    except Exception:
        pass

    fallback_candidates = [
        urljoin(site_root, "/sitemap.xml"),
        urljoin(site_root, "/sitemap_index.xml"),
        urljoin(site_root, "/sitemap.txt"),
    ]

    for candidate in fallback_candidates:
        if candidate not in found:
            try:
                r = fetch(candidate)
                if r.ok and r.text.strip():
                    found.append(candidate)
            except Exception:
                pass

    # de-dupe, preserve order
    deduped = []
    seen = set()
    for item in found:
        item = canonicalize_url(item, strip_query=False)
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_sitemap(sitemap_url: str) -> dict:
    r = fetch(sitemap_url)
    r.raise_for_status()
    text = r.text.strip()

    # Plain text sitemap
    if text and not text.startswith("<") and "\n" in text:
        urls = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(canonicalize_url(line))
        return {"type": "urlset", "page_urls": urls, "child_sitemaps": []}

    root = ET.fromstring(text)

    if localname(root.tag) == "sitemapindex":
        child_sitemaps = []
        for el in root.iter():
            if localname(el.tag) == "loc" and el.text:
                child_sitemaps.append(canonicalize_url(el.text.strip(), strip_query=False))
        return {"type": "index", "page_urls": [], "child_sitemaps": child_sitemaps}

    if localname(root.tag) == "urlset":
        page_urls = []
        for url_el in root.iter():
            if localname(url_el.tag) == "loc" and url_el.text:
                page_urls.append(canonicalize_url(url_el.text.strip()))
        return {"type": "urlset", "page_urls": page_urls, "child_sitemaps": []}

    return {"type": "unknown", "page_urls": [], "child_sitemaps": []}


def inspect_sitemap_branches(site_root: str, layers: int = 2) -> dict:
    root_sitemaps = discover_sitemaps(site_root)
    rows = []
    queue = deque((sm, 1) for sm in root_sitemaps)
    seen = set()

    while queue:
        sitemap_url, layer = queue.popleft()
        if sitemap_url in seen or layer > layers:
            continue
        seen.add(sitemap_url)

        try:
            parsed = parse_sitemap(sitemap_url)
            rows.append(
                {
                    "layer": layer,
                    "sitemap_url": sitemap_url,
                    "kind": parsed["type"],
                    "child_sitemaps": len(parsed["child_sitemaps"]),
                    "page_urls": len(parsed["page_urls"]),
                }
            )
            if parsed["type"] == "index":
                for child in parsed["child_sitemaps"]:
                    queue.append((child, layer + 1))
        except Exception as e:
            rows.append(
                {
                    "layer": layer,
                    "sitemap_url": sitemap_url,
                    "kind": "error",
                    "child_sitemaps": 0,
                    "page_urls": 0,
                    "error": str(e),
                }
            )

    return {
        "site_root": site_root,
        "root_sitemaps": root_sitemaps,
        "branches": rows,
    }


def collect_all_urls_from_sitemaps(site_root: str) -> list[str]:
    root_sitemaps = discover_sitemaps(site_root)
    if not root_sitemaps:
        return []

    seen_sitemaps = set()
    seen_urls = set()
    stack = list(root_sitemaps)

    while stack:
        sitemap_url = stack.pop()
        if sitemap_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap_url)

        try:
            parsed = parse_sitemap(sitemap_url)
            if parsed["type"] == "index":
                for child in parsed["child_sitemaps"]:
                    if child not in seen_sitemaps:
                        stack.append(child)
            elif parsed["type"] == "urlset":
                for page_url in parsed["page_urls"]:
                    if same_site(page_url, site_root):
                        seen_urls.add(page_url)
        except Exception:
            continue

    return sorted(seen_urls)


def looks_like_asset(url: str) -> bool:
    return bool(
        re.search(
            r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|mp4|mp3|css|js|json|xml)$",
            url,
            re.IGNORECASE,
        )
    )


def crawl_sitewide(site_root: str, max_pages: int = 500) -> list[str]:
    start = canonicalize_url(site_root)
    queue = deque([start])
    visited = set()
    found = set()

    while queue and len(found) < max_pages:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        try:
            r = fetch(current)
            content_type = r.headers.get("Content-Type", "").lower()
            if not r.ok or "text/html" not in content_type:
                continue
        except Exception:
            continue

        found.add(current)

        try:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue

                child = canonicalize_url(urljoin(current, href))
                if not same_site(child, site_root):
                    continue
                if looks_like_asset(child):
                    continue
                if child not in visited:
                    queue.append(child)
        except Exception:
            continue

    return sorted(found)


st.set_page_config(page_title="Simple Sitemap Tool", layout="wide")
st.title("Simple Sitemap Branch + URL Pull Tool")

url = st.text_input("Enter website URL", placeholder="https://example.com")
site_root = normalize_site_url(url) if url else ""

col1, col2, col3 = st.columns(3)

with col1:
    run_l1 = st.button("Show sitemap branches: layer 1", use_container_width=True)

with col2:
    run_l2 = st.button("Show sitemap branches: layer 2", use_container_width=True)

with col3:
    run_all = st.button("Pull all URLs sitewide", use_container_width=True)

max_pages = st.number_input("Crawl fallback max pages", min_value=50, max_value=5000, value=500, step=50)

if run_l1 or run_l2:
    if not site_root:
        st.error("Enter a URL first.")
    else:
        layers = 1 if run_l1 else 2
        with st.spinner("Inspecting sitemap tree..."):
            result = inspect_sitemap_branches(site_root, layers=layers)

        st.subheader("Root sitemap files")
        st.json(result["root_sitemaps"])

        st.subheader(f"Sitemap branches up to layer {layers}")
        st.dataframe(result["branches"], use_container_width=True)

if run_all:
    if not site_root:
        st.error("Enter a URL first.")
    else:
        with st.spinner("Pulling sitewide URLs..."):
            urls = collect_all_urls_from_sitemaps(site_root)

            source = "sitemap"
            if not urls:
                source = "crawler fallback"
                urls = crawl_sitewide(site_root, max_pages=max_pages)

        st.subheader(f"URLs found via {source}")
        st.write(f"Count: {len(urls)}")
        st.dataframe([{"url": u} for u in urls], use_container_width=True)
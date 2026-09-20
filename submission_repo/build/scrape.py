"""Scraper. STUB. Workshop 1 block 4.

Crawl both websites, extract the readable text, and collect image
records in the same pass. Run this file directly to (re)build
data/pages.json and data/images.json.

Check for /sitemap.xml before writing a crawler. If it exists it lists
every page and you can skip the crawl entirely.
"""
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SITES = [
    # TODO: the two Inno Wing sites you were given
    "https://innowings.engg.hku.hk/",
    "https://innoacademy.engg.hku.hk/",
]


def crawl(start_url: str, max_pages: int = 500) -> list[dict]:
    """Download and extract pages from the same site as start_url."""
    seen, queue, pages = set(), [start_url], []
    domain = urlparse(start_url).netloc

    blocked_extensions = ( #added by student to avoid downloading non-html files
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
        ".zip", ".doc", ".docx", ".ppt", ".pptx",
    )

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            response = requests.get(url, timeout=20)
            #------------------
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                continue
            #------------------
            html = response.text
            pages.append(extract(html, url))
        except Exception as exc:
            print("skipped", url, exc)
            continue

        if len(pages) == 1 or len(pages) % 10 == 0:
            print(f"[{domain}] {len(pages)} pages collected")

        for a in BeautifulSoup(html, "html.parser").select("a[href]"):
            parsed = urlparse(urljoin(url, a["href"]))
            link = parsed._replace(query="", fragment="").geturl()
            path = parsed.path.lower()
            if (
                parsed.scheme in ("http", "https")
                and parsed.netloc == domain
                and link not in seen
                and not path.endswith(blocked_extensions)
                and "/wp-admin" not in path
                and "/wp-login" not in path
            ):
                queue.append(link)

    print(f"[{domain}] finished with {len(pages)} pages")
    return pages


def extract(html: str, url: str) -> dict:
    """Return {"url", "title", "text", "images": [...]} for one page.

    soup.get_text() on the whole page returns the navigation menu and
    footer on every page. Those near-identical fragments become chunks
    that look moderately similar to every query and crowd real results
    out of your top five. Open the site, right-click the content, choose
    Inspect, and find the element that actually wraps it.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.select("script, style, nav, header, footer, noscript"):
        tag.decompose()

    body = (
        soup.select_one("main")
        or soup.select_one("article")
        or soup.select_one("#content")
        or soup.select_one(".site-content")
        or soup.body
        or soup
    )

    images = []
    for img in soup.select("img"):
        src = img.get("src")
        if not src:
            continue
        fig = img.find_parent("figure")
        images.append({
            "src":     urljoin(url, src),     # relative -> absolute
            "alt":     img.get("alt", ""),
            "caption": (fig.find("figcaption").get_text(strip=True)
                        if fig and fig.find("figcaption") else ""),
            "page":    url,
        })

    return {
        "url":    url,
        "title":  soup.title.get_text(strip=True) if soup.title else "",
        "text":   body.get_text(" ", strip=True),
        "images": images,
    }


if __name__ == "__main__":
    pages = []
    for site in SITES:
        pages.extend(crawl(site))

    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(pages, indent=1), encoding="utf-8")

    images = [im for p in pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1), encoding="utf-8")

    print(f"{len(pages)} pages, {len(images)} images")

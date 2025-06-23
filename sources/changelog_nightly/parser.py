import re, requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RX_REPO = re.compile(r"^https://github\.com/([^/]+)/([^/]+)$")
EXCLUDE = {"https://github.com/thechangelog", "https://github.com/trending"}

def fetch(url: str) -> BeautifulSoup:
    logger.info(f"Fetching URL: {url}")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    logger.info(f"Fetched {len(r.text)} bytes from {url}")
    return BeautifulSoup(r.text, "html.parser")

def parse_page(page_url: str) -> list[dict]:
    logger.info(f"Parsing page: {page_url}")
    soup  = fetch(page_url)
    links = [a["href"] for a in soup.find_all("a", href=True)]
    logger.info(f"Found {len(links)} links on page")
    rows  = []
    for href in links:
        full = requests.compat.urljoin(page_url, href)
        if any(full.startswith(bad) for bad in EXCLUDE):
            logger.debug(f"Excluded link: {full}")
            continue
        # follow HEAD  to detect GitHub redirect
        try:
            head = requests.head(full, allow_redirects=True, timeout=5)
            final = head.url
            logger.debug(f"HEAD {full} -> {final}")
        except requests.RequestException as e:
            logger.warning(f"HEAD request failed for {full}: {e}")
            continue
        m = RX_REPO.match(final)
        if not m:
            logger.debug(f"Not a repo link: {final}")
            continue
        owner, repo = m.groups()
        row = {
            "source"      : "CHANGELOG_NIGHTLY",
            "external_id" : f"{owner}/{repo}",
            "item_type"   : "project",
            "title"       : repo,
            "url"         : final,
            "meta"    : {"origin_url": full},
            "scraped_at"  : datetime.utcnow().isoformat()
        }
        logger.info(f"Parsed repo: {row}")
        rows.append(row)
    logger.info(f"Returning {len(rows)} parsed rows")
    return rows
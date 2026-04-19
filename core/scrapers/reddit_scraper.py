# core/scrapers/reddit_scraper.py
"""
Scraper assíncrono de OSINT via API pública do Reddit.

"""
import asyncio
import logging
from typing import Optional

import aiohttp

from core.config import DEFAULT_CONFIG as cfg

logger = logging.getLogger(__name__)

_USER_AGENT = "KojiX-CTI-Scanner/2.0 (automated OSINT research tool)"


def _extrair_post(post_data: dict) -> Optional[dict]:

    titulo = post_data.get("title", "").strip()
    texto = post_data.get("selftext", "").strip()
    url_externa = post_data.get("url_overridden_by_dest", "") or post_data.get("url", "")

    if titulo in ("[removed]", "[deleted]", ""):
        return None

    if texto in ("[removed]", "[deleted]"):
        texto = ""

    
    if len(texto) < cfg.MIN_TEXT_LENGTH:
        titulo_minimo = max(20, cfg.MIN_TEXT_LENGTH // 2)
        if len(titulo) < titulo_minimo:
            return None

        texto = f"Post sem corpo relevante. Contexto derivado do título: {titulo}"
        if url_externa and "reddit.com" not in url_externa:
            texto += f" | Fonte externa: {url_externa}"

    if len(texto) > cfg.MAX_TEXT_LENGTH:
        texto = texto[: cfg.MAX_TEXT_LENGTH].rsplit(" ", 1)[0] + "..."

    return {
        "fonte": "reddit",
        "titulo": titulo,
        "texto_completo": texto,
        "url": f"https://reddit.com{post_data.get('permalink', '')}",
        "url_externa": url_externa,
        "autor": post_data.get("author", ""),
        "upvotes": post_data.get("ups", 0),
        "subreddit": post_data.get("subreddit", ""),
        "created_utc": post_data.get("created_utc", 0),
    }


async def _fetch_subreddit(
    session: aiohttp.ClientSession,
    search_term: str,
    subreddit: str,
    limit: int,
) -> list[dict]:
    """Busca posts de um único subreddit de forma assíncrona."""
    url = f"https://old.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": search_term,
        "restrict_sr": "on",
        "limit": limit,
        "sort": "relevance",
        "t": "year",
    }
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with session.get(
            url,
            headers=headers,
            params=params,
            timeout=aiohttp.ClientTimeout(total=cfg.REDDIT_TIMEOUT_SECONDS),
        ) as response:
            if response.status != 200:
                logger.warning(
                    "Reddit r/%s respondeu HTTP %d. Pulando.", subreddit, response.status
                )
                return []

            data = await response.json(content_type=None)
            return data.get("data", {}).get("children", [])

    except asyncio.TimeoutError:
        logger.warning("Timeout ao acessar r/%s. Pulando.", subreddit)
        return []
    except aiohttp.ClientError as e:
        logger.error("Erro de rede em r/%s: %s", subreddit, e)
        return []


async def scrape_reddit_osint(
    search_term: str,
    subreddits: Optional[list[str]] = None,
    limit_per_subreddit: int = cfg.REDDIT_LIMIT_PER_SUBREDDIT,
) -> list[dict]:
    
    alvos = subreddits or list(cfg.REDDIT_SUBREDDITS)
    logger.info("Reddit OSINT: '%s' em %s", search_term, alvos)

    async with aiohttp.ClientSession() as session:
        # Dispara todas as buscas de subreddits simultaneamente
        tasks = [
            _fetch_subreddit(session, search_term, sub, limit_per_subreddit)
            for sub in alvos
        ]
        resultados = await asyncio.gather(*tasks, return_exceptions=False)

    posts_brutos: list[dict] = []
    urls_vistas: set[str] = set()

    for subreddit, children in zip(alvos, resultados):
        logger.info("r/%s: %d resultados brutos.", subreddit, len(children))
        for child in children:
            post = _extrair_post(child.get("data", {}))
            if post is None or post["url"] in urls_vistas:
                continue
            urls_vistas.add(post["url"])
            posts_brutos.append(post)

    if not posts_brutos:
        logger.error("Reddit: nenhum post válido coletado para '%s'.", search_term)
        return []

    ordenados = sorted(posts_brutos, key=lambda p: p["upvotes"], reverse=True)
    logger.info("Reddit: %d posts úteis coletados.", len(ordenados))
    return ordenados

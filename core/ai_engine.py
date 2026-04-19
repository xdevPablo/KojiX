# core/ai_engine.py
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

from core.agents import quant_agent, recon_agent, strat_agent
from core.cache import ReportCache
from core.config import DEFAULT_CONFIG as cfg
from core.scrapers.nvd_scraper import scrape_nvd, formatar_nvd_para_prompt
from core.scrapers.reddit_scraper import scrape_reddit_osint
from core.telemetry import THREAT_KEYWORDS, calcular_telemetria, formatar_telemetria_para_prompt

_RAIZ_PROJETO = Path(__file__).parent.parent
load_dotenv(_RAIZ_PROJETO / ".env")

logger = logging.getLogger(__name__)

_PROMPT_VERSIONS = {
    "recon_agent": "2026-04-18",
    "quant_agent": "2026-04-18",
    "strat_agent": "2026-04-18",
}

# Phase callback type: (phase_idx: int, done: bool) -> None
PhaseCallback = Callable[[int, bool], None]


# =============================================================================
# Corpus preparation helpers
# =============================================================================

def _normalizar_subreddits(subreddits: Optional[list[str]] = None) -> list[str]:
    """Returns the final list of subreddits in stable order for cache/context."""
    return sorted(subreddits or list(cfg.REDDIT_SUBREDDITS))


def _build_cache_context(
    subreddits: Optional[list[str]] = None,
    include_nvd: bool = True,
) -> dict:
    """Minimum context that defines the analytical equivalence of a cached report."""
    return {
        "gemini_model": cfg.GEMINI_DEFAULT_MODEL,
        "include_nvd": include_nvd,
        "thread_limit": cfg.LIMITE_THREADS,
        "reddit_limit_per_subreddit": cfg.REDDIT_LIMIT_PER_SUBREDDIT,
        "subreddits": _normalizar_subreddits(subreddits),
        "prompt_versions": _PROMPT_VERSIONS,
    }


def _persistir_raw_data(
    search_term: str,
    threads: list[dict],
    cves_nvd: list[dict],
    probabilidades: dict[str, float],
) -> None:
    """
    Saves the raw snapshot of the execution in a structured format.

    Keeps Reddit and NVD separate to avoid incorrect recalculations in standalone mode.
    """
    payload = {
        "schema_version": 2,
        "generated_at": datetime.utcnow().isoformat(),
        "search_term": search_term,
        "reddit_threads": threads,
        "nvd_cves": cves_nvd,
        "telemetry": probabilidades,
    }
    cfg.base_dir.mkdir(parents=True, exist_ok=True)
    with open(cfg.raw_data, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _selecionar_threads_relevantes(posts: list[dict]) -> list[dict]:
    """Selects subset of posts by upvotes (credibility proxy)."""
    if len(posts) <= cfg.LIMITE_THREADS:
        return posts
    selecionados = sorted(posts, key=lambda p: p.get("upvotes", 0), reverse=True)
    selecionados = selecionados[: cfg.LIMITE_THREADS]
    logger.info(
        "Reddit subset: %d/%d threads | upvotes: %d–%d",
        cfg.LIMITE_THREADS, len(posts),
        selecionados[-1].get("upvotes", 0),
        selecionados[0].get("upvotes", 0),
    )
    return selecionados


def _formatar_corpus_reddit(posts: list[dict]) -> str:
    """Serializes posts for insertion into the Recon Agent prompt."""
    partes = []
    for idx, post in enumerate(posts, start=1):
        partes.append(
            f"\n--- THREAD {idx} [Reddit r/{post.get('subreddit','?')}]"
            f" | upvotes: {post.get('upvotes', 0)} ---\n"
            f"TITLE: {post.get('titulo', '')}\n"
            f"TEXT: {post.get('texto_completo', '')}\n"
        )
    return "".join(partes)


# =============================================================================
# Python section generators (zero API tokens)
# =============================================================================

def _gerar_secao_6_cves(cves: list[dict]) -> str:
    """
    Section 6: Vulnerability Log — raw NVD data, investigative format.
    Tables removed — structured list by criticality, more readable in PDF.
    """
    if not cves:
        return (
            "\n\n## 6. Vulnerability Log (NVD/NIST)\n\n"
            "_No CVEs with CVSS >= 7.0 found for this term._\n"
        )

    criticas  = [c for c in cves if (c.get("cvss_score") or 0) >= 9.0]
    altas     = [c for c in cves if 7.0 <= (c.get("cvss_score") or 0) < 9.0]

    linhas = [
        "\n\n## 6. Vulnerability Log (NVD/NIST)\n",
        f"Source: National Vulnerability Database (NIST)  |  "
        f"Query: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC  |  "
        f"Total High/Critical: **{len(cves)}** "
        f"({len(criticas)} critical, {len(altas)} high)\n",
    ]

    def _bloco_cve(cve: dict, idx: int) -> list[str]:
        cve_id   = cve.get("cve_id", "CVE-UNKNOWN")
        score    = cve.get("cvss_score", "N/A")
        sev      = cve.get("cvss_severidade", "N/A")
        vetor    = cve.get("vetor_ataque", "N/A")
        pub      = cve.get("publicado_em", "N/A")
        desc     = cve.get("descricao", "Not available.")
        refs     = cve.get("referencias", [])

        nivel = "CRITICAL" if (score or 0) >= 9.0 else "HIGH"

        bloco = [
            f"\n### {idx}. {cve_id}",
            f"**CVSS:** {score}  |  **Severity:** {nivel}  |  "
            f"**Vector:** {vetor}  |  **Published:** {pub}\n",
            f"{desc}\n",
        ]
        if refs:
            bloco.append("**References:**")
            for r in refs[:2]:
                bloco.append(f"- {r}")
        bloco.append("\n---")
        return bloco

    if criticas:
        linhas.append("\n### CRITICALITY: CRITICAL (CVSS >= 9.0)\n")
        for i, c in enumerate(criticas, 1):
            linhas.extend(_bloco_cve(c, i))

    if altas:
        linhas.append(f"\n### CRITICALITY: HIGH (CVSS 7.0 – 8.9)\n")
        offset = len(criticas)
        for i, c in enumerate(altas, offset + 1):
            linhas.extend(_bloco_cve(c, i))

    return "\n".join(linhas)


def _gerar_secao_7_osint(threads: list[dict]) -> str:
    """
    Section 7: OSINT Sources — compact list of analyzed threads.
    """
    if not threads:
        return (
            "\n\n## 7. Analyzed OSINT Sources\n\n"
            "_No threads collected from Reddit._\n"
        )

    linhas = [
        "\n\n## 7. Analyzed OSINT Sources (Reddit)\n",
        f"Total threads selected by relevance (upvotes): **{len(threads)}**\n",
    ]

    for i, t in enumerate(threads, 1):
        titulo   = t.get("titulo", "No title")[:90]
        sub      = t.get("subreddit", "?")
        upvotes  = t.get("upvotes", 0)
        url      = t.get("url", "#")
        linhas.append(
            f"{i}. **{titulo}** "
            f"[r/{sub} · {upvotes} pts]  \n"
            f"   {url}\n"
        )

    return "\n".join(linhas)


def _gerar_secao_8_telemetria_expandida(
    threads: list[dict],
    probabilidades: dict[str, float],
) -> str:
    """
    Section 8: Signal Telemetry — keyword frequency per vector.
    """
    if not probabilidades:
        return ""

    texto_global = " ".join(
        f"{p.get('texto_completo', '')} {p.get('titulo', '')}"
        for p in threads
    ).lower()

    blocos = []
    for vetor, prob in probabilidades.items():
        keywords = THREAT_KEYWORDS.get(vetor, [])
        contagens = {kw: texto_global.count(kw) for kw in keywords if texto_global.count(kw) > 0}
        if not contagens:
            continue
        total = sum(contagens.values())
        kw_str = "  |  ".join(
            f"`{kw}` x{n}" for kw, n in
            sorted(contagens.items(), key=lambda x: x[1], reverse=True)[:6]
        )
        blocos.append(
            f"**{vetor}** — {prob}% ({total} occurrences)\n{kw_str}\n"
        )

    if not blocos:
        return ""

    linhas = [
        "\n\n## 8. Signal Telemetry by Vector\n",
        f"Corpus: {len(threads)} Reddit threads  |  "
        f"Analysis: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n",
    ]
    linhas.extend(blocos)
    return "\n".join(linhas)


def _gerar_secao_9_indice_referencias(
    cves: list[dict],
    threads: list[dict],
    search_term: str,
) -> str:
    
    linhas = [
        "\n\n## 9. Source Index\n",
        f"Investigated term: **{search_term}** |  "
        f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n",
    ]

    if cves:
        linhas.append("**NVD/NIST — Official Vulnerabilities**\n")
        for c in cves:
            cve_id = c.get("cve_id", "")
            score  = c.get("cvss_score", "N/A")
            linhas.append(
                f"- {cve_id} (CVSS {score}) — "
                f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            )

    if threads:
        linhas.append("\n**Reddit OSINT — Threads**\n")
        for t in threads:
            titulo  = t.get("titulo", "")[:70]
            url     = t.get("url", "#")
            upvotes = t.get("upvotes", 0)
            linhas.append(f"- [{titulo}]({url}) — {upvotes} pts")

    linhas.append(
        "\n---\n"
        "Data source: NVD CVE API 2.0 (NIST) + Reddit OSINT (Public API)  |  "
        "Engine: Google Gemini  |  Classification: TLP:AMBER\n"
    )

    return "\n".join(linhas)


def _montar_apendice_completo(
    cves: list[dict],
    threads: list[dict],
    probabilidades: dict[str, float],
    search_term: str,
) -> str:
    
    secao_6 = _gerar_secao_6_cves(cves)
    secao_7 = _gerar_secao_7_osint(threads)
    secao_8 = _gerar_secao_8_telemetria_expandida(threads, probabilidades)
    secao_9 = _gerar_secao_9_indice_referencias(cves, threads, search_term)

    return f"{secao_6}{secao_7}{secao_8}{secao_9}"


# =============================================================================
# Main Pipeline
# =============================================================================

async def analyze_threat_data(
    search_term: str,
    subreddits: Optional[list[str]] = None,
    output_filepath: Optional[str] = None,
    force_refresh: bool = False,
    include_nvd: bool = True,
    phase_callback: Optional[PhaseCallback] = None,
) -> tuple[bool, dict]:
    
    caminho_saida = Path(output_filepath) if output_filepath else cfg.report_md
    cache_context = _build_cache_context(subreddits, include_nvd=include_nvd)

    def _phase(idx: int, done: bool = False) -> None:
        """Emits phase event safely (callback is optional)."""
        if phase_callback is not None:
            try:
                phase_callback(idx, done)
            except Exception as e:
                logger.warning("phase_callback error (idx=%d done=%s): %s", idx, done, e)

    # -------------------------------------------------------------------------
    # Cache check — zero tokens if valid hit
    # -------------------------------------------------------------------------
    cache = ReportCache()

    if not force_refresh:
        hit = cache.get(
            search_term,
            max_age_days=cfg.CACHE_MAX_AGE_DAYS,
            context=cache_context,
        )
        if hit:
            logger.info(
                "Cache HIT for '%s' (id=%d, generated on %s). Use --force to regenerate.",
                search_term, hit["id"], hit["created_at"][:10],
            )
            # Marks all phases as completed immediately (cache hit)
            for i in range(4):
                _phase(i, done=False)
                _phase(i, done=True)
            caminho_saida.parent.mkdir(parents=True, exist_ok=True)
            with open(caminho_saida, "w", encoding="utf-8") as f:
                f.write(hit["report_md"])
            return True, hit.get("telemetry", {})

    # -------------------------------------------------------------------------
    # Credentials
    # -------------------------------------------------------------------------
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not found. Configure the .env file")
        return False, {}

    # -------------------------------------------------------------------------
    # PHASE 0: Parallel Scraping (Reddit + NVD simultaneously)
    # -------------------------------------------------------------------------
    _phase(0, done=False)  # COLLECT -> active

    if include_nvd:
        logger.info("\n[PHASE 1: Parallel Collection — Reddit + NVD]")
        posts_reddit, cves_nvd = await asyncio.gather(
            scrape_reddit_osint(search_term, subreddits=subreddits),
            scrape_nvd(search_term),
            return_exceptions=False,
        )
    else:
        logger.info("\n[PHASE 1: Collection — Reddit only (NVD disabled)]")
        posts_reddit = await scrape_reddit_osint(search_term, subreddits=subreddits)
        cves_nvd = []

    posts_reddit = posts_reddit or []
    cves_nvd     = cves_nvd or []

    if not posts_reddit and not cves_nvd:
        logger.error("No source returned data. Pipeline aborted.")
        _phase(0, done=False)  # keeps as error (GUI will use _err_fase in callback)
        return False, {}

    if not posts_reddit:
        logger.warning("Reddit without data — continuing with NVD only.")
    if include_nvd and not cves_nvd:
        logger.warning("NVD without data — continuing with Reddit only.")

    _phase(0, done=True)  # COLLECT -> completed

    # -------------------------------------------------------------------------
    # Data preparation
    # -------------------------------------------------------------------------
    threads        = _selecionar_threads_relevantes(posts_reddit)
    corpus_reddit  = _formatar_corpus_reddit(threads)
    dados_nvd_str  = formatar_nvd_para_prompt(cves_nvd)
    probabilidades = calcular_telemetria(threads) if threads else {}
    telemetria_str = formatar_telemetria_para_prompt(probabilidades)

    _persistir_raw_data(search_term, threads, cves_nvd, probabilidades)

    logger.info(
        "Corpus: %d Reddit threads + %d NVD CVEs -> %d total items",
        len(threads), len(cves_nvd), len(threads) + len(cves_nvd),
    )

    # -------------------------------------------------------------------------
    # PHASE 1: Recon Agent -> Sections 1-3
    # -------------------------------------------------------------------------
    _phase(1, done=False)  # RECON -> active
    logger.info("\n[PHASE 2: Recon Agent -> Sections 1-3]")

    secoes_iniciais = await recon_agent.run(corpus_reddit, dados_nvd_str, gemini_key)
    if not secoes_iniciais:
        logger.error("Recon Agent failed. Pipeline aborted.")
        return False, probabilidades

    _phase(1, done=True)  # RECON -> completed

    logger.info("Cooldown %ds...", cfg.INTER_AGENT_COOLDOWN_SECONDS)
    await asyncio.sleep(cfg.INTER_AGENT_COOLDOWN_SECONDS)

    # -------------------------------------------------------------------------
    # PHASE 2: Quant Agent -> Section 4
    # -------------------------------------------------------------------------
    _phase(2, done=False)  # ANALYTICS -> active
    logger.info("\n[PHASE 3: Quant Agent -> Section 4]")

    secao_telemetria = await quant_agent.run(telemetria_str, secoes_iniciais, gemini_key)
    if not secao_telemetria:
        logger.error("Quant Agent failed. Pipeline aborted.")
        return False, probabilidades

    _phase(2, done=True)  # ANALYTICS -> completed

    dossie_parcial = f"{secoes_iniciais}\n\n{secao_telemetria}"

    logger.info("Cooldown %ds...", cfg.INTER_AGENT_COOLDOWN_SECONDS)
    await asyncio.sleep(cfg.INTER_AGENT_COOLDOWN_SECONDS)

    # -------------------------------------------------------------------------
    # PHASE 3: Strat Agent -> Section 5
    # -------------------------------------------------------------------------
    _phase(3, done=False)  # STRATEGY -> active
    logger.info("\n[PHASE 4: Strat Agent -> Section 5]")

    secao_estrategica = await strat_agent.run(dossie_parcial, gemini_key)
    if not secao_estrategica:
        logger.warning("Strat Agent failed. Using partial dossier.")
        secao_estrategica = ""

    _phase(3, done=True)  # STRATEGY -> completed

    relatorio_ia = f"{dossie_parcial}\n\n{secao_estrategica}".strip()

    # -------------------------------------------------------------------------
    # PHASE 4 : Technical Appendix -> Sections 6-9 — ZERO API tokens
    # -------------------------------------------------------------------------
    logger.info("\n[PHASE 5: Technical Appendix -> Sections 6-9 (Pure Python, 0 tokens)]")

    apendice = _montar_apendice_completo(
        cves=cves_nvd,
        threads=threads,
        probabilidades=probabilidades,
        search_term=search_term,
    )

    secoes_geradas = sum([
        bool(cves_nvd),
        bool(threads),
        bool(probabilidades),
        True,
    ])
    logger.info("Appendix generated: %d additional sections without API cost.", secoes_geradas)

    relatorio_final = f"{relatorio_ia}\n\n{apendice}"

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(relatorio_final)

    logger.info("Complete dossier saved to: %s", caminho_saida)

    cache.save(
        search_term=search_term,
        telemetria=probabilidades,
        report_md=relatorio_final,
        post_count=len(threads),
        context=cache_context,
    )
    cache.purge_old(max_age_days=cfg.CACHE_PURGE_AFTER_DAYS)

    return True, probabilidades


# =============================================================================
# Synchronous helper for standalone exporter
# =============================================================================

def carregar_telemetria_do_disco(json_filepath: Optional[str] = None) -> dict[str, float]:
    """Synchronous helper: loads and calculates telemetry from disk without calling API."""
    caminho = Path(json_filepath) if json_filepath else cfg.raw_data
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            telemetria = data.get("telemetry")
            if isinstance(telemetria, dict):
                return telemetria

            reddit_threads = data.get("reddit_threads", [])
            if isinstance(reddit_threads, list):
                return calcular_telemetria(reddit_threads)

            return {}

        if isinstance(data, list):
            reddit_threads = [
                item for item in data
                if isinstance(item, dict) and item.get("fonte") == "reddit"
            ]
            return calcular_telemetria(reddit_threads)

        return {}
    except Exception as e:
        logger.error("Failed to load telemetry: %s", e)
        return {}
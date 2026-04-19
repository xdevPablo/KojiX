# core/scrapers/nvd_scraper.py

import asyncio
import logging
import os
from typing import Optional

import aiohttp

from core.config import DEFAULT_CONFIG as cfg

logger = logging.getLogger(__name__)


def _extrair_cvss(metricas: dict) -> tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Extrai pontuação CVSS, severidade e vetor de ataque das métricas de uma CVE.
    Tenta CVSSv3.1, CVSSv3.0 e CVSSv2 em cascata (preferência pela versão mais recente).

    Returns:
        Tupla (base_score, severity, attack_vector) ou (None, None, None) se ausente.
    """
    
    for chave_metrica in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entradas = metricas.get(chave_metrica, [])
        if not entradas:
            continue
        dados = entradas[0].get("cvssData", {})
        score = dados.get("baseScore")
        severity = dados.get("baseSeverity") or dados.get("baseSeverity", "").upper()
        vector = dados.get("attackVector") or dados.get("accessVector")
        return score, severity, vector

    return None, None, None


def _extrair_descricao_en(descriptions: list[dict]) -> str:
    """Extrai descrição em inglês da lista de descrições multilíngues da CVE."""
    for desc in descriptions:
        if desc.get("lang") == "en":
            texto = desc.get("value", "").strip()
            # Trunca para controle de tokens, preservando sentido
            if len(texto) > 400:
                texto = texto[:400].rsplit(".", 1)[0] + "."
            return texto
    return "Descrição não disponível."


def _estruturar_cve(item: dict) -> Optional[dict]:
    cve = item.get("cve", {})
    cve_id = cve.get("id", "")

    if not cve_id:
        return None

    descriptions = cve.get("descriptions", [])
    descricao = _extrair_descricao_en(descriptions)

    metricas = cve.get("metrics", {})
    score, severidade, vetor_ataque = _extrair_cvss(metricas)

    publicado_em = cve.get("published", "")[:10]

    referencias = [
        ref.get("url", "")
        for ref in cve.get("references", [])[:3]  # Máximo 3 referências
        if ref.get("url")
    ]

    return {
        "fonte": "nvd",
        "cve_id": cve_id,
        "descricao": descricao,
        "cvss_score": score,
        "cvss_severidade": severidade,
        "vetor_ataque": vetor_ataque,
        "publicado_em": publicado_em,
        "referencias": referencias,
        # Campo unificado para compatibilidade com o pipeline de texto
        "titulo": f"{cve_id} — CVSS {score or 'N/A'} ({severidade or 'N/A'})",
        "texto_completo": (
            f"[NVD OFICIAL] {cve_id} | CVSS: {score} ({severidade}) | "
            f"Vetor: {vetor_ataque or 'N/A'} | Publicado: {publicado_em}\n"
            f"Descrição: {descricao}"
        ),
    }


async def scrape_nvd(
    search_term: str,
    results_per_page: int = cfg.NVD_RESULTS_PER_PAGE,
) -> list[dict]:
    
    nvd_api_key = os.getenv("NVD_API_KEY")

    headers = {"User-Agent": "KojiX-CTI-Scanner/2.0"}
    if nvd_api_key:
        headers["apiKey"] = nvd_api_key

    params = {
        "keywordSearch": search_term,
        "resultsPerPage": results_per_page,
    }

    logger.info("NVD: consultando CVEs para '%s'...", search_term)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                cfg.NVD_API_BASE_URL,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=cfg.NVD_TIMEOUT_SECONDS),
            ) as response:
                if response.status == 403:
                    logger.warning(
                        "NVD retornou 403 — rate limit atingido. "
                        "Configure NVD_API_KEY no .env para 50 req/30s."
                    )
                    return []

                if response.status != 200:
                    logger.error(
                        "NVD API respondeu HTTP %d para '%s'.",
                        response.status, search_term,
                    )
                    return []

                data = await response.json(content_type=None)

    except asyncio.TimeoutError:
        logger.warning("NVD: timeout após %ds para '%s'.", cfg.NVD_TIMEOUT_SECONDS, search_term)
        return []
    except aiohttp.ClientError as e:
        logger.error("NVD: erro de rede: %s", e)
        return []

    vulnerabilidades_brutas = data.get("vulnerabilities", [])
    total_resultados = data.get("totalResults", 0)

    logger.info(
        "NVD: %d CVEs encontradas (total disponível: %d).",
        len(vulnerabilidades_brutas), total_resultados,
    )

    if not vulnerabilidades_brutas:
        logger.info("NVD: nenhuma CVE encontrada para '%s'.", search_term)
        return []

    cves_estruturadas = []
    for item in vulnerabilidades_brutas:
        cve = _estruturar_cve(item)
        if cve is None:
            continue

        score = cve.get("cvss_score")
        if score is not None and score < 7.0:
            logger.debug("CVE %s ignorada (CVSS %.1f < 7.0)", cve["cve_id"], score)
            continue

        cves_estruturadas.append(cve)

    cves_estruturadas.sort(
        key=lambda c: c.get("cvss_score") or 0.0,
        reverse=True,
    )

    logger.info(
        "NVD: %d CVEs com CVSS >= 7.0 selecionadas para análise.",
        len(cves_estruturadas),
    )
    return cves_estruturadas


def formatar_nvd_para_prompt(cves: list[dict]) -> str:
    
    if not cves:
        return "Nenhuma CVE oficial encontrada para este termo no NVD/NIST."

    linhas = ["=== VULNERABILIDADES OFICIAIS (NVD/NIST) ==="]
    for cve in cves:
        score_str = f"CVSS {cve['cvss_score']}" if cve["cvss_score"] else "CVSS N/A"
        sev_str = cve["cvss_severidade"] or "N/A"
        vetor_str = cve["vetor_ataque"] or "N/A"
        linhas.append(
            f"\n• {cve['cve_id']} | {score_str} ({sev_str}) | Vetor: {vetor_str}"
            f"\n  Publicado: {cve['publicado_em']}"
            f"\n  Descrição: {cve['descricao']}"
        )

    return "\n".join(linhas)
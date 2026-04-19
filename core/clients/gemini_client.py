# core/clients/gemini_client.py

import asyncio
import logging
import random
from typing import Optional

import aiohttp

from core.config import DEFAULT_CONFIG as cfg

logger = logging.getLogger(__name__)

_SAFETY_SETTINGS = [
    {"category": cat, "threshold": "BLOCK_NONE"}
    for cat in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _extrair_texto_gemini(data: dict) -> Optional[str]:
    """Navega a estrutura de resposta da API Gemini e extrai o texto gerado."""
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        finish_reason = (data.get("candidates") or [{}])[0].get("finishReason", "UNKNOWN")
        logger.error(
            "Resposta Gemini inesperada. finishReason=%s | raw=%s",
            finish_reason, str(data)[:300],
        )
        return None


def _calcular_backoff(attempt: int) -> float:
    """Calcula backoff exponencial com jitter e teto máximo."""
    return min(
        cfg.API_BACKOFF_BASE_SECONDS * (2 ** attempt) + random.uniform(0, 5),
        cfg.API_BACKOFF_MAX_SECONDS,
    )


async def chamar_gemini(
    prompt: str,
    api_key: str,
    model: str = cfg.GEMINI_DEFAULT_MODEL,
    max_retries: int = cfg.API_MAX_RETRIES,
    max_output_tokens: int = cfg.API_MAX_OUTPUT_TOKENS,
) -> Optional[str]:
    """
    Envia um prompt para o Gemini e retorna o texto gerado (assíncrono).

    - I/O não-bloqueante via aiohttp
    - asyncio.sleep no backoff (event loop nunca para)
    - Backoff exponencial com jitter + teto máximo
    - Retry em 429 e 5xx; falha imediata em 4xx não-retryable
    - maxOutputTokens para forçar respostas econômicas
    - temperature=0.4 para favorecer precisão técnica

    Args:
        prompt:            Texto do prompt.
        api_key:           Chave de API do Google AI Studio.
        model:             Identificador do modelo Gemini.
        max_retries:       Tentativas máximas.
        max_output_tokens: Limite de tokens de output (padrão: 1500).

    Returns:
        Texto gerado ou None em falha definitiva.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models"
        f"/{model}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": _SAFETY_SETTINGS,
        "generationConfig": {
            "maxOutputTokens": max_output_tokens,
            "temperature": 0.4,
            "topP": 0.9,
        },
    }

    timeout = aiohttp.ClientTimeout(total=90)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(max_retries):
            try:
                async with session.post(url, headers=headers, json=payload) as response:

                    if response.status in _RETRYABLE_STATUS:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            wait = float(retry_after)
                        else:
                            wait = _calcular_backoff(attempt)
                        logger.warning(
                            "Gemini HTTP %d — backoff %.0fs (tentativa %d/%d)",
                            response.status, wait, attempt + 1, max_retries,
                        )
                        await asyncio.sleep(wait)
                        continue

                    if response.status != 200:
                        body = await response.text()
                        logger.error(
                            "Gemini HTTP %d (não retryable): %s",
                            response.status, body[:200],
                        )
                        return None

                    data = await response.json(content_type=None)
                    return _extrair_texto_gemini(data)

            except asyncio.TimeoutError:
                logger.warning("Gemini timeout (tentativa %d/%d).", attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    await asyncio.sleep(_calcular_backoff(attempt))

            except aiohttp.ClientError as e:
                logger.warning(
                    "Erro de conexão com Gemini (tentativa %d/%d): %s",
                    attempt + 1, max_retries, e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(_calcular_backoff(attempt))
                    continue
                logger.error("Gemini: falha definitiva de conexão após %d tentativas.", max_retries)
                return None

    logger.error("Gemini: %d tentativas excedidas. Abortando.", max_retries)
    return None

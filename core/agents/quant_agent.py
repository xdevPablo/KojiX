# core/agents/quant_agent.py
"""
Agente Analítico Quantitativo — Fase 2 do pipeline CTI.
Refatoração: síncrono → assíncrono.
"""
import logging
from typing import Optional

from core.clients.gemini_client import chamar_gemini

logger = logging.getLogger(__name__)


async def run(
    telemetria_str: str,
    contexto_anterior: str,
    api_key: str,
) -> Optional[str]:
    """
    Gera a Seção 4 (Auditoria Quantitativa) do dossiê CTI.

    Args:
        telemetria_str:    Probabilidades formatadas por formatar_telemetria_para_prompt().
        contexto_anterior: Seções 1-3 já redigidas pelo recon_agent.
        api_key:           Chave de API do Gemini.

    Returns:
        Texto da Seção 4 ou None em falha.
    """
    logger.info("[Quant Agent] Correlacionando telemetria probabilística...")

    prompt = f"""Você é um Analista de Risco de CTI. Seja DIRETO e TÉCNICO.

REGRA DE FORMATO:
- Nenhum parágrafo com mais de 3 linhas
- Use listas Markdown para agrupamentos
- Sem tabelas

<telemetria_osint>
{telemetria_str}
</telemetria_osint>

<contexto_tatico>
{contexto_anterior}
</contexto_tatico>

<instrucoes>
Redija a seção "## 4. Auditoria Quantitativa e Estimativa de Risco":

- Liste os vetores por ordem de probabilidade (já fornecida)
- Para o vetor dominante: explique em até 3 linhas por que lidera o ranking
- Correlacione cada vetor com as CVEs oficiais mencionadas no contexto (se houver)
- Finalize com: "Alocação de Recursos Blue Team Recomendada" em lista de prioridades (máx. 5 itens)

Inicie imediatamente:
</instrucoes>"""

    resposta = await chamar_gemini(prompt, api_key)

    if not resposta:
        logger.error("[Quant Agent] Falha — nenhuma resposta do modelo.")
        return None

    return resposta.strip()
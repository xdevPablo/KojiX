# core/agents/strat_agent.py

import logging
from typing import Optional

from core.clients.gemini_client import chamar_gemini

logger = logging.getLogger(__name__)


async def run(dossie_parcial: str, gemini_key: str) -> Optional[str]:
    """
    Gera Seção 5 (Recomendações) e consolida o dossiê final.

    Args:
        dossie_parcial: Seções 1-4 já redigidas pelos agentes anteriores.
        gemini_key:     Chave de API do Gemini.

    Returns:
        Dossiê completo em Markdown ou None em falha.
    """
    logger.info("[Strat Agent] Sintetizando conclusão executiva...")

    prompt = f"""Você é um Analista Sênior de CTI finalizando um dossiê técnico de inteligência de ameaças.

REGRAS DE FORMATO:
- Parágrafos de 4 a 6 linhas com análise técnica real
- Listas Markdown para ações — nunca texto corrido onde uma lista resolve
- Proibido tabelas Markdown e tags HTML
- NÃO reescreva as seções anteriores — gere EXCLUSIVAMENTE a Seção 5
- Tom: investigativo e técnico, não corporativo

<dossie_parcial>
{dossie_parcial}
</dossie_parcial>

<instrucoes>
Gere APENAS a Seção 5. O Python concatena com as seções anteriores automaticamente.

## 5. Avaliacao de Risco e Diretivas de Resposta

**Nivel de Risco Atual:** [CRITICO / ALTO / MEDIO / BAIXO]
Parágrafo de 4 a 6 linhas justificando o nivel atribuido com base nos vetores identificados,
nas CVEs encontradas e nos padroes de comportamento observados nas threads OSINT.

**Vetor Primario de Ameaca:**
- Nome do vetor dominante e por que lidera
- CVE mais severa associada (se identificada) com score CVSS
- Técnica MITRE ATT&CK correspondente

**Diretivas de Contencao Imediata:**
- Liste 5 a 7 acoes tecnicas especificas e executaveis agora
- Cada item no formato: [URGENCIA] Acao — O que fazer tecnicamente — Mitiga: CVE ou TTP
- Urgencias: CRITICA / ALTA / MEDIA
- Proibido acoes genericas como "treine usuarios" ou "atualize sistemas"
- Cada acao deve ser especifica o suficiente para um engenheiro executar sem interpretacao

**Lacunas de Inteligencia Identificadas:**
- Liste 2 a 4 informacoes que NAO foi possivel confirmar com os dados coletados
- Indique qual fonte adicional poderia preencher cada lacuna (ex: logs de SIEM, threat feeds pagos, honeypots)

Gere apenas a Secao 5. Inicie imediatamente:
</instrucoes>"""

    resultado = await chamar_gemini(prompt, gemini_key)

    if not resultado:
        logger.error("[Strat Agent] Falha — nenhuma resposta do modelo.")
        return None

    return resultado.strip()
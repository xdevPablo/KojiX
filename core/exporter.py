# core/exporter.py
"""
Módulo de exportação de artefatos executivos CTI.

Responsabilidade: Gerar gráficos de telemetria e compilar o relatório PDF final.

"""
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

import markdown
import matplotlib
import matplotlib.pyplot as plt
from fpdf import FPDF

from core.config import DEFAULT_CONFIG as cfg

matplotlib.use("Agg")  # Backend não-interativo para geração em servidor/pipeline

logger = logging.getLogger(__name__)


# =============================================================================
# CTIReport — definida no escopo de MÓDULO (não dentro de função)
# =============================================================================
class CTIReport(FPDF):
    """
    Subclasse de FPDF com cabeçalho e rodapé personalizados para o dossiê CTI.
    Definida no escopo de módulo para evitar recriação a cada chamada de função.
    """
    HEADER_TEXT = "KojiX - Cyber Threat Intelligence"
    CLASSIFICATION_TEXT = "TLP:AMBER — Distribuição Restrita: Blue Team / SecOps"

    def header(self) -> None:
        # Página de capa (1) não recebe cabeçalho
        if self.page_no() <= 1:
            return
        self.set_font("helvetica", "B", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, self.HEADER_TEXT, border=False, align="R")
        self.ln(10)

    def footer(self) -> None:
        # Página de capa não recebe número de página
        if self.page_no() <= 1:
            return
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")


# =============================================================================
# Sanitização de texto
# =============================================================================
_REPLACEMENTS: dict[str, str] = {
    "\u2013": "-",    # en dash
    "\u2014": "-",    # em dash
    "\u201c": '"',    # aspas tipográficas abertas
    "\u201d": '"',    # aspas tipográficas fechadas
    "\u2018": "'",    # aspas simples abertas
    "\u2019": "'",    # aspas simples fechadas (apóstrofo tipográfico)
    "\u2026": "...",  # ellipsis
    "\u2022": "-",    # bullet
    "\u2122": "TM",   # trademark
    "\u00ae": "(R)",  # registered
    "\u00a9": "(C)",  # copyright
}


def sanitize_text_for_pdf(text: str) -> str:
    """
    Normaliza caracteres tipográficos para equivalentes ASCII seguros.

    Usa decomposição NFKD para converter acentuados (é → e) sem
    perda silenciosa de dados. O encode/decode latin-1 com 'ignore'
    foi REMOVIDO pois descartava caracteres silenciosamente.
    """
    for original, substituto in _REPLACEMENTS.items():
        text = text.replace(original, substituto)

    # Decompõe via NFKD: 'é' → 'e' + combining accent → mantém só ASCII
    normalizado = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalizado if ord(c) < 128)


# =============================================================================
# Geração de gráfico de telemetria
# =============================================================================
def generate_telemetry_chart(
    probabilidades: dict[str, float],
    chart_filepath: Optional[str] = None,
) -> bool:
    """
    Gera o gráfico de barras horizontais de estimativa de vetores de ataque.

    IMPORTANTE: Recebe probabilidades já calculadas (dict) — NÃO relê do disco.
    Isso elimina I/O redundante e possíveis race conditions com o ai_engine.

    Args:
        probabilidades: Dicionário {vetor: probabilidade%} (output de calcular_telemetria).
        chart_filepath:  Caminho de saída da imagem. Usa default do config se None.

    Returns:
        True em sucesso, False em falha.
    """
    if not probabilidades:
        logger.warning("Telemetria vazia — gráfico não gerado.")
        return False

    caminho = chart_filepath or str(cfg.telemetry_chart)

    try:
        # Ordena do menor para o maior para gráfico de barras horizontais legível
        dados_ordenados = dict(sorted(probabilidades.items(), key=lambda x: x[1]))

        plt.figure(figsize=(10, 5.5))
        barras = plt.barh(
            list(dados_ordenados.keys()),
            list(dados_ordenados.values()),
            color="#1A5276",
            edgecolor="black",
        )

        for barra in barras:
            largura = barra.get_width()
            plt.text(
                largura + 0.5,
                barra.get_y() + barra.get_height() / 2,
                f"{largura}%",
                va="center", ha="left",
                fontsize=11, fontweight="bold",
                color="#922B21",
            )

        plt.title(
            "Estimativa Probabilística de Vetores de Ataque (Base OSINT)",
            fontsize=14, fontweight="bold", pad=15,
        )
        plt.xlabel("Probabilidade de Ocorrência/Foco (%)", fontsize=11)
        plt.grid(axis="x", linestyle="--", alpha=0.3)

        max_val = max(dados_ordenados.values()) if dados_ordenados else 10
        plt.xlim(0, max_val * 1.2)

        plt.tight_layout()
        plt.savefig(caminho, dpi=250)
        plt.close()

        logger.info("Gráfico de telemetria gerado em: %s", caminho)
        return True

    except Exception as e:
        logger.error("Erro na geração do gráfico: %s", e, exc_info=True)
        plt.close()  # Garante que a figura seja fechada mesmo em erro
        return False


# =============================================================================
# Geração de capa do PDF
# =============================================================================
def _adicionar_capa(pdf: CTIReport) -> None:
    """Renderiza a página de capa do dossiê CTI."""
    pdf.add_page()

    # Título principal
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 40, "", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 15, "CYBER THREAT INTELLIGENCE", align="C", new_x="LMARGIN", new_y="NEXT")

    # Subtítulo
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(139, 0, 0)
    pdf.cell(0, 15, "Dossie Tatico OSINT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 20, "", new_x="LMARGIN", new_y="NEXT")

    # Assinatura do pipeline
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Gerado por Pipeline Multi-Agente (KojiX)", align="C", new_x="LMARGIN", new_y="NEXT")

    # Metodologia (rodapé da capa)
    pdf.set_y(-80)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "Metodologia de Coleta:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(
        0, 6,
        "Os dados deste dossie sao baseados em inferencia probabilistica sobre "
        "comunicacoes ativas em foruns OSINT (Reddit: r/cybersecurity, r/netsec, r/blueteamsec). "
        "O modelo quantifica vetores de ataque, e os Agentes de IA interpretam o cenario "
        "para formular estrategias defensivas. Distribuicao restrita para equipes Blue Team/SecOps."
    )

    # Classificação
    pdf.set_y(-30)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "CLASSIFICACAO: TLP:AMBER", align="C", new_x="LMARGIN", new_y="NEXT")


# =============================================================================
# Pipeline HTML → PDF
# =============================================================================
def _converter_markdown_para_html(md_text: str) -> str:
    """
    Converte Markdown para HTML e aplica correções de formatação para FPDF.
    Centraliza todos os regex em um único lugar para facilitar manutenção.
    """
    html = markdown.markdown(md_text, extensions=["tables"])

    # Correções de tabelas malformadas (duplicatas de tags)
    html = re.sub(r"(<td[^>]*>)(?:\s*<td[^>]*>)+", r"\1", html, flags=re.IGNORECASE)
    html = re.sub(r"(</td\s*>)(?:\s*</td\s*>)+", r"\1", html, flags=re.IGNORECASE)
    html = re.sub(r"(<th[^>]*>)(?:\s*<th[^>]*>)+", r"\1", html, flags=re.IGNORECASE)
    html = re.sub(r"(</th\s*>)(?:\s*</th\s*>)+", r"\1", html, flags=re.IGNORECASE)

    # Remove tags <p> aninhadas em células de tabela
    html = re.sub(r"<td>\s*<p>(.*?)</p>\s*</td>", r"<td>\1</td>", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<th>\s*<p>(.*?)</p>\s*</th>", r"<th>\1</th>", html, flags=re.IGNORECASE | re.DOTALL)

    # Espaçamento após headings e listas
    html = re.sub(r"(</h[1-6]>)", r"\1<br>", html, flags=re.IGNORECASE)
    html = re.sub(r"</?(ul|ol)>", "<br>", html, flags=re.IGNORECASE)
    html = re.sub(r"<li>(.*?)</li>", r"&nbsp;&nbsp;&nbsp; - \1<br><br>", html, flags=re.IGNORECASE | re.DOTALL)
    html = html.replace("</p>", "</p><br>")

    return html


def generate_pdf_report(
    md_filepath: Optional[str] = None,
    probabilidades: Optional[dict[str, float]] = None,
    pdf_filepath: Optional[str] = None,
) -> bool:
    """
    Compila o relatório PDF executivo a partir do Markdown gerado pelo pipeline.

    Args:
        md_filepath:     Caminho do arquivo .md de entrada.
        probabilidades:  Dict de telemetria já calculado (evita releitura de disco).
                         Se None, tenta calcular a partir do raw_data.json.
        pdf_filepath:    Caminho de saída do PDF.

    Returns:
        True em sucesso, False em falha.
    """
    caminho_md = Path(md_filepath) if md_filepath else cfg.report_md
    caminho_pdf = Path(pdf_filepath) if pdf_filepath else cfg.report_pdf
    caminho_chart = cfg.telemetry_chart

    if not caminho_md.exists():
        logger.error("Arquivo Markdown não encontrado: %s", caminho_md)
        return False

    logger.info("\n[FASE 4: Geração de Artefato Executivo]")

    # Se probabilidades não foram passadas, calcula a partir do disco (modo standalone)
    if probabilidades is None:
        logger.info("Calculando telemetria a partir do disco (modo standalone)...")
        from core.ai_engine import carregar_telemetria_do_disco
        probabilidades = carregar_telemetria_do_disco()

    # Evita reaproveitar um gráfico antigo caso a geração atual falhe.
    if caminho_chart.exists():
        try:
            caminho_chart.unlink()
        except OSError as e:
            logger.warning("Não foi possível remover gráfico anterior: %s", e)

    # Gera gráfico com dados em memória — sem I/O redundante
    logger.info("Gerando gráfico de telemetria...")
    grafico_gerado = False
    if probabilidades:
        grafico_gerado = generate_telemetry_chart(probabilidades, str(caminho_chart))
    else:
        logger.info("Sem telemetria disponível para este relatório — gráfico será omitido.")

    logger.info("Compilando layout executivo do PDF...")
    try:
        with open(caminho_md, "r", encoding="utf-8") as f:
            md_text = f.read()

        md_text_sanitizado = sanitize_text_for_pdf(md_text)
        html_text = _converter_markdown_para_html(md_text_sanitizado)

        # Injeta o gráfico após o heading da Seção 4
        # Usa forward slashes explicitamente — FPDF interpreta o src como URL
        # e não aceita backslash (quebra no Windows)
        chart_src = str(caminho_chart).replace("\\", "/")
        if grafico_gerado and caminho_chart.exists():
            injecao_grafico = (
                f'\\1<br><br><center><img src="{chart_src}" width="180"></center><br><br>'
            )
            html_text = re.sub(
                r"(<h2[^>]*>4\..*?</h2\s*>)",
                injecao_grafico,
                html_text,
                flags=re.IGNORECASE,
            )

        # Monta o PDF
        pdf = CTIReport()
        pdf.set_auto_page_break(auto=True, margin=15)

        _adicionar_capa(pdf)

        pdf.add_page()
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.write_html(html_text)

        caminho_pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(caminho_pdf))

        logger.info("SUCESSO: Relatório dinâmico gerado em: %s", caminho_pdf)
        return True

    except Exception as e:
        logger.error("Falha na renderização estrutural do PDF: %s", e, exc_info=True)
        return False

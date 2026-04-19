# core/telemetry.py

THREAT_KEYWORDS: dict[str, list[str]] = {
    "Evasão de Defesas (EDR/AV)": ["edr", "bypass", "antivirus", "av evasion", "amsi"],
    "Exploração de Vulnerabilidades": ["cve", "exploit", "patch", "zero-day", "rce", "lpe"],
    "Impacto em Backups": ["backup", "shadow copy", "vss", "restore", "wbadmin"],
    "Engenharia Social / Phishing": ["phishing", "social engineering", "spear", "pretexting"],
    "Negociação e Resgate": ["negotiat", "ransom", "pay", "bitcoin", "monero", "decryptor"],
    "Movimento Lateral": ["lateral movement", "pass-the-hash", "pth", "kerberoast", "mimikatz"],
}


def calcular_telemetria(posts: list[dict]) -> dict[str, float]:
    """
    Calcula a estimativa de probabilidade de cada vetor de ameaça
    baseada na densidade de keywords no corpus OSINT fornecido.

    Args:
        posts: Lista de posts com campos 'texto_completo' e 'titulo'.

    Returns:
        Dicionário {vetor: probabilidade_percentual} ordenado do maior para o menor.
        Retorna dicionário vazio se não houver posts.
    """
    if not posts:
        return {}

    # Concatena todo o corpus em uma única string lowercase para eficiência
    texto_global = " ".join(
        f"{p.get('texto_completo', '')} {p.get('titulo', '')}"
        for p in posts
    ).lower()

    contagens: dict[str, int] = {
        vetor: sum(texto_global.count(kw) for kw in keywords)
        for vetor, keywords in THREAT_KEYWORDS.items()
    }

    contagens_positivas = {
        vetor: contagem
        for vetor, contagem in contagens.items()
        if contagem > 0
    }
    if not contagens_positivas:
        return {}

    total_sinais = sum(contagens_positivas.values())

    probabilidades = {
        vetor: round((contagem / total_sinais) * 100, 1)
        for vetor, contagem in contagens_positivas.items()
    }

    # Ordena do vetor de maior probabilidade para o menor
    return dict(sorted(probabilidades.items(), key=lambda x: x[1], reverse=True))


def formatar_telemetria_para_prompt(probabilidades: dict[str, float]) -> str:
    """Serializa as probabilidades para inserção em prompts de LLM."""
    if not probabilidades:
        return "Nenhum sinal detectado no corpus."
    return "\n".join(f"- {vetor}: {prob}%" for vetor, prob in probabilidades.items())

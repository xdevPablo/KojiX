# core/config.py
from pathlib import Path
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PipelineConfig:
   
    base_dir: Path = field(default_factory=lambda: Path("data"))

    # --- Limites operacionais ---
    LIMITE_THREADS: int = 15
    MIN_TEXT_LENGTH: int = 50
    MAX_TEXT_LENGTH: int = 800
    REDDIT_TIMEOUT_SECONDS: int = 15
    REDDIT_LIMIT_PER_SUBREDDIT: int = 100
    REDDIT_SUBREDDITS: tuple[str, ...] = ("cybersecurity", "netsec", "blueteamsec")

    # --- Configuração de API (apenas Gemini) ---
    GEMINI_DEFAULT_MODEL: str = "gemini-2.5-flash"
    API_MAX_RETRIES: int = 5
    API_BACKOFF_BASE_SECONDS: int = 15
    API_BACKOFF_MAX_SECONDS: int = 120
    API_MAX_TOKENS: int = 4096
    API_MAX_OUTPUT_TOKENS: int = 4096       # Elevado: suporta seções longas sem truncar
    INTER_AGENT_COOLDOWN_SECONDS: int = 15

    # --- NVD (National Vulnerability Database / NIST) ---
    NVD_API_BASE_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    NVD_RESULTS_PER_PAGE: int = 10          # Free tier: max 5 req/30s sem API key
    NVD_TIMEOUT_SECONDS: int = 20

    # --- Cache SQLite ---
    CACHE_MAX_AGE_DAYS: int = 7
    CACHE_PURGE_AFTER_DAYS: int = 30

    # --- Paths derivados (propriedades calculadas) ---
    @property
    def raw_data(self) -> Path:
        return self.base_dir / "raw_data.json"

    @property
    def report_md(self) -> Path:
        return self.base_dir / "report_output.md"

    @property
    def report_pdf(self) -> Path:
        return self.base_dir / "report_output.pdf"

    @property
    def telemetry_chart(self) -> Path:
        return self.base_dir / "telemetry.png"

    @property
    def cache_db(self) -> Path:
        return self.base_dir / "kojix_cache.db"


# Instância padrão — importada diretamente pelos módulos
DEFAULT_CONFIG = PipelineConfig()
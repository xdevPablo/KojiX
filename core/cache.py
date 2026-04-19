# core/cache.py
"""
Sistema de cache persistente para relatórios CTI — baseado em SQLite.

Objetivo: eliminar chamadas redundantes à API Gemini para termos de busca
já analisados recentemente.

Arquitetura:
    - SQLite local (sem servidor, sem dependências extras)
    - Busca por cache_key (hash de search_term + contexto analítico)
    - Armazena: telemetria, relatório markdown completo, metadados
    - Histórico completo consultável via list_reports()

IMPORTANTE: O índice de cache_key é criado DENTRO da migration,
não no _SCHEMA_SQL, para evitar falha quando a tabela já existe
sem essa coluna (bancos criados em versões anteriores).
"""
import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from core.config import DEFAULT_CONFIG as cfg

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = 2
_CACHE_KEY_VERSION = 1

# ─── Schema base ─────────────────────────────────────────────────────────────
# NUNCA coloque aqui índices que dependem de colunas adicionadas por migration.
# Índices de colunas adicionadas via ALTER TABLE pertencem a _migrate_reports_table.
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    search_term     TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    post_count      INTEGER NOT NULL DEFAULT 0,
    telemetry_json  TEXT,
    report_md       TEXT NOT NULL,
    top_vector      TEXT,
    top_vector_pct  REAL
);

CREATE INDEX IF NOT EXISTS idx_reports_term_date
    ON reports (search_term, created_at DESC);
"""


class ReportCache:
    """
    Interface de alto nível para o cache SQLite de relatórios CTI.

    Uso típico:
        cache = ReportCache()
        hit = cache.get("ransomware", max_age_days=7, context={...})
        if hit:
            return hit["report_md"]
        # ... gera relatório ...
        cache.save("ransomware", telemetria, report_md, context={...})
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(db_path) if db_path else cfg.base_dir / "kojix_cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ──────────────────────────────────────────────────────────────────────────
    # Inicialização
    # ──────────────────────────────────────────────────────────────────────────
    def _init_db(self) -> None:
        """Cria as tabelas base e aplica migrations incrementais."""
        with self._connect() as conn:
            # 1. Garante tabelas base (nunca usa colunas de migration aqui)
            conn.executescript(_SCHEMA_SQL)
            # 2. Aplica colunas e índices adicionais de forma idempotente
            self._migrate_reports_table(conn)
            # 3. Registra versão do schema
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
                (_SCHEMA_VERSION, datetime.utcnow().isoformat()),
            )
        logger.debug("Cache inicializado em: %s", self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate_reports_table(self, conn: sqlite3.Connection) -> None:
        """
        Adiciona colunas e índices ausentes de forma idempotente.

        REGRA: qualquer índice que dependa de uma coluna adicionada via
        ALTER TABLE deve ser criado AQUI, nunca em _SCHEMA_SQL.
        """
        colunas = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(reports)").fetchall()
        }

        # cache_key — identifica unicamente o contexto analítico do relatório
        if "cache_key" not in colunas:
            conn.execute("ALTER TABLE reports ADD COLUMN cache_key TEXT")
            logger.debug("Migration: coluna cache_key adicionada.")

        # context_json — contexto completo serializado (auditoria)
        if "context_json" not in colunas:
            conn.execute("ALTER TABLE reports ADD COLUMN context_json TEXT")
            logger.debug("Migration: coluna context_json adicionada.")

        # Índice só criado DEPOIS das colunas existirem com certeza
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reports_cache_key_date "
            "ON reports (cache_key, created_at DESC)"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Utilitários
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _normalize_search_term(search_term: str) -> str:
        return search_term.lower().strip()

    @classmethod
    def build_cache_key(
        cls,
        search_term: str,
        context: Optional[dict] = None,
    ) -> str:
        """Gera chave estável que representa o contexto analítico do relatório."""
        normalized_context = context or {}
        context_blob = json.dumps(
            normalized_context,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        raw_key = f"{cls._normalize_search_term(search_term)}|{context_blob}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"v{_CACHE_KEY_VERSION}:{digest}"

    # ──────────────────────────────────────────────────────────────────────────
    # Leitura
    # ──────────────────────────────────────────────────────────────────────────
    def get(
        self,
        search_term: str,
        max_age_days: int = 7,
        context: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Busca o relatório mais recente para o termo, se ainda for fresco.

        Quando `context` é fornecido, usa cache_key (hash do contexto analítico)
        para evitar reutilizar relatório incompatível com os parâmetros atuais.
        Caso contrário faz fallback por search_term + data.
        """
        cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
        normalized_term = self._normalize_search_term(search_term)
        cache_key = self.build_cache_key(search_term, context) if context is not None else None

        with self._connect() as conn:
            if cache_key is not None:
                row = conn.execute(
                    """
                    SELECT id, search_term, cache_key, created_at, post_count,
                           telemetry_json, context_json, report_md,
                           top_vector, top_vector_pct
                    FROM reports
                    WHERE cache_key = ? AND created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (cache_key, cutoff),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT id, search_term, cache_key, created_at, post_count,
                           telemetry_json, context_json, report_md,
                           top_vector, top_vector_pct
                    FROM reports
                    WHERE search_term = ? AND created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (normalized_term, cutoff),
                ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["telemetry"] = json.loads(result.pop("telemetry_json") or "{}")
        result["context"]   = json.loads(result.pop("context_json")   or "{}")
        logger.info(
            "Cache HIT para '%s' (id=%d, gerado em %s, %s dias atrás)",
            search_term,
            result["id"],
            result["created_at"][:10],
            (datetime.utcnow() - datetime.fromisoformat(result["created_at"])).days,
        )
        return result

    def list_reports(self, limit: int = 50) -> list[dict]:
        """Lista relatórios do mais recente ao mais antigo."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, search_term, created_at, post_count,
                       top_vector, top_vector_pct
                FROM reports
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, report_id: int) -> Optional[dict]:
        """Recupera relatório completo pelo ID (para re-exportar PDF sem API)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["telemetry"] = json.loads(result.pop("telemetry_json") or "{}")
        # context_json pode não existir em registros antigos
        if "context_json" in result:
            result["context"] = json.loads(result.pop("context_json") or "{}")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Escrita
    # ──────────────────────────────────────────────────────────────────────────
    def save(
        self,
        search_term: str,
        telemetria: dict[str, float],
        report_md: str,
        post_count: int = 0,
        context: Optional[dict] = None,
    ) -> int:
        """
        Persiste um novo relatório no cache.

        Returns:
            ID do registro inserido.
        """
        top_vector    = next(iter(telemetria), None)
        top_pct       = telemetria.get(top_vector, 0.0) if top_vector else 0.0
        normalized    = self._normalize_search_term(search_term)
        context_json  = json.dumps(context or {}, ensure_ascii=False, sort_keys=True)
        cache_key     = self.build_cache_key(search_term, context)

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reports
                    (search_term, cache_key, created_at, post_count,
                     telemetry_json, context_json,
                     report_md, top_vector, top_vector_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized,
                    cache_key,
                    datetime.utcnow().isoformat(),
                    post_count,
                    json.dumps(telemetria, ensure_ascii=False),
                    context_json,
                    report_md,
                    top_vector,
                    top_pct,
                ),
            )
            report_id: int = cursor.lastrowid or 0

        logger.info(
            "Relatório salvo no cache (id=%d, term='%s', posts=%d)",
            report_id, search_term, post_count,
        )
        return report_id

    def delete(self, report_id: int) -> bool:
        """Remove um relatório específico do cache."""
        with self._connect() as conn:
            affected = conn.execute(
                "DELETE FROM reports WHERE id = ?", (report_id,)
            ).rowcount
        return affected > 0

    def purge_old(self, max_age_days: int = 30) -> int:
        """Remove relatórios mais velhos que max_age_days. Retorna quantidade removida."""
        cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
        with self._connect() as conn:
            affected = conn.execute(
                "DELETE FROM reports WHERE created_at < ?", (cutoff,)
            ).rowcount
        logger.info("Purge: %d relatórios antigos removidos.", affected)
        return affected
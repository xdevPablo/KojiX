# gui.py
"""
KojiX CTI Hub — Graphical Interface v1.0.0

"""
import asyncio
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from dotenv import load_dotenv, set_key
from tkinter import messagebox
from PIL import Image
from core.ai_engine import analyze_threat_data
from core.cache import ReportCache
from core.config import DEFAULT_CONFIG as cfg
from core.exporter import generate_pdf_report

# ─────────────────────────────────────────────────────────────────────────────
ENV_PATH = Path(".env")
load_dotenv(ENV_PATH)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────────────────────────────────────
# KojiX Brand Palette — ops room dark red / charcoal / steel
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":            "#08080d",
    "panel":         "#0e0f16",
    "card":          "#12131b",
    "card_alt":      "#171924",
    "border":        "#202433",
    "border_hi":     "#31374a",

    "red":           "#8f1d27",
    "red_hover":     "#a82a35",
    "red_dim":       "#4d1117",
    "red_bg":        "#21090d",
    "red_glow":      "#17090d",

    "white":         "#d8deea",
    "silver":        "#c3cede",
    "silver_dim":    "#667387",
    "silver_muted":  "#323847",

    "green":         "#3ac97c",
    "green_dim":     "#0e2417",
    "amber":         "#c8942b",
    "amber_dim":     "#241a09",

    "console_bg":    "#06070b",
    "console_red":   "#c2cedf",
    "console_dim":   "#4e596b",
    "console_ok":    "#3ac97c",
    "console_white": "#d8deea",
}

FASES = [
    ("COLLECT",   "Reddit + NVD",  15),
    ("RECON",     "Agent 1",       60),
    ("ANALYTICS", "Agent 2",       45),
    ("STRATEGY",  "Agent 3",       45),
    ("REPORT",    "PDF",           10),
]

_FASE_LOG_START = [
    "",                                            
    "Recon Agent → analyzing corpus (Sections 1-3)...",   
    "Quant Agent → quantitative audit (Section 4)...", 
    "Strat Agent → strategic directives (Section 5)...", 
]

_FASE_LOG_DONE = [
    "Collection completed.",         # 0
    "Recon completed.",              # 1
    "Analytics completed.",          # 2
    "Strategy completed.",           # 3
]

_FASE_STATUS = [
    ("●  COLLECTING...",  "amber"),
    ("●  RECON...",       "amber"),
    ("●  ANALYTICS...",   "amber"),
    ("●  STRATEGY...",    "amber"),
]

_FASE_PROGRESS = [0.18, 0.45, 0.65, 0.85]

TOKEN_EST_INPUT  = 18_000
TOKEN_EST_OUTPUT = 10_000

WINDOW_W = 860
WINDOW_H = 820


# ─────────────────────────────────────────────────────────────────────────────
def _severity_color(pct: Optional[float]) -> str:
    if pct is None:
        return C["silver_dim"]
    if pct >= 60:
        return C["red_hover"]
    if pct >= 35:
        return C["amber"]
    return C["green"]


def _open_file(path: Path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")


def _fmt_seconds(s: int) -> str:
    if s < 60:
        return f"{s}s"
    return f"{s // 60}m {s % 60:02d}s"


def _arquivar_sessao(alvo: str) -> Optional[Path]:
    
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = f"{alvo.replace(' ', '_')}_{ts}"
        dest = cfg.base_dir / "historico" / nome
        dest.mkdir(parents=True, exist_ok=True)

        pdf_nome = f"Dossier_{alvo.replace(' ', '_')}.pdf"
        mapa = {
            cfg.raw_data:        cfg.raw_data.name,
            cfg.report_md:       cfg.report_md.name,
            cfg.telemetry_chart: cfg.telemetry_chart.name,
            cfg.report_pdf:      pdf_nome,
        }
        pdf_dest = None
        for origem, nome_dest in mapa.items():
            if origem.exists():
                destino = dest / nome_dest
                shutil.move(str(origem), str(destino))
                if nome_dest == pdf_nome:
                    pdf_dest = destino
        return pdf_dest
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Phase Tracker
# ─────────────────────────────────────────────────────────────────────────────
class PhaseTracker(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C["card"], corner_radius=8,
                         border_color=C["border"], border_width=1, **kwargs)
        self.grid_columnconfigure(tuple(range(len(FASES))), weight=1)

        self._inds:  "list[ctk.CTkLabel]" = []
        self._names: "list[ctk.CTkLabel]" = []
        self._subs:  "list[ctk.CTkLabel]" = []

        for i, (nome, sub, _) in enumerate(FASES):
            col = ctk.CTkFrame(self, fg_color="transparent")
            col.grid(row=0, column=i, padx=6, pady=10, sticky="nsew")
            col.grid_columnconfigure(0, weight=1)

            ind = ctk.CTkLabel(col, text="○",
                               font=ctk.CTkFont(family="Consolas", size=20),
                               text_color=C["silver_muted"])
            ind.grid(row=0, column=0)
            self._inds.append(ind)

            lbl = ctk.CTkLabel(col, text=nome,
                               font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
                               text_color=C["silver_muted"])
            lbl.grid(row=1, column=0)
            self._names.append(lbl)

            sub_l = ctk.CTkLabel(col, text=sub,
                                 font=ctk.CTkFont(family="Consolas", size=8),
                                 text_color=C["silver_muted"], wraplength=90)
            sub_l.grid(row=2, column=0)
            self._subs.append(sub_l)

            if i < len(FASES) - 1:
                ctk.CTkLabel(self, text="──",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=C["silver_muted"]).grid(
                    row=0, column=i, sticky="e")

    def set_collect_mode(self, include_nvd: bool):
        """Atualiza o subtítulo da fase de coleta para refletir a fonte real."""
        if self._subs:
            self._subs[0].configure(text="Reddit + NVD" if include_nvd else "Reddit only")

    def reset(self):
        for i, (_, sub, _) in enumerate(FASES):
            self._inds[i].configure(text="○", text_color=C["silver_muted"])
            self._names[i].configure(text_color=C["silver_muted"])
            self._subs[i].configure(text=sub, text_color=C["silver_muted"])

    def set_active(self, idx: int):
        if 0 <= idx < len(FASES):
            self._inds[idx].configure(text="◉", text_color=C["amber"])
            self._names[idx].configure(text_color=C["amber"])
            self._subs[idx].configure(text_color=C["amber"])

    def set_done(self, idx: int):
        if 0 <= idx < len(FASES):
            self._inds[idx].configure(text="●", text_color=C["green"])
            self._names[idx].configure(text_color=C["green"])
            self._subs[idx].configure(text_color=C["silver_dim"])

    def set_error(self, idx: int):
        if 0 <= idx < len(FASES):
            self._inds[idx].configure(text="✕", text_color=C["red_hover"])
            self._names[idx].configure(text_color=C["red_hover"])


# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────
class KojiXApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KojiX — Cyber Threat Intelligence")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])

        caminho_icone = Path("assets/icone.ico")
        if caminho_icone.exists():
            self.iconbitmap(str(caminho_icone))

        self._running        = False
        self._ultimo_pdf: Optional[Path] = None
        self._fase_atual     = -1
        self._t_inicio       = 0.0
        self._timer_job: Optional[str] = None
        self._include_nvd    = True

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_tabs()
        self._build_statusbar()

    # ── Header ───────────────────────────────────────────────────────────────
    def _build_header(self):
        frame = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0)
        frame.grid(row=0, column=0, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            frame, text="●",
            font=ctk.CTkFont(size=16),
            text_color=C["green"], width=30,
        )
        self._dot.grid(row=0, column=0, rowspan=2, padx=(22, 0), pady=20)

        ctk.CTkLabel(
            frame, text="HUB",
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
            text_color=C["red"],
        ).grid(row=0, column=1, padx=14, sticky="sw", pady=(14, 0))

        ctk.CTkLabel(
            frame,
            text="Autonomous Cyber Threat Intelligence Engine  ·  NVD/NIST × Reddit OSINT  ·  Gemini AI",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=C["silver_dim"],
        ).grid(row=1, column=1, padx=14, sticky="nw", pady=(0, 14))

        caminho_logo = Path("assets/logo.png")
        if caminho_logo.exists():
            from PIL import Image
            img_logo = ctk.CTkImage(
                light_image=Image.open(caminho_logo),
                dark_image=Image.open(caminho_logo),
                size=(180, 180))
            lbl_logo = ctk.CTkLabel(frame, text="", image=img_logo)
            lbl_logo.grid(row=0, column=2, rowspan=2, padx=(10, 10), pady=(10, 10), sticky="e")

        ctk.CTkLabel(
            frame, text="v1.0.0",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=C["red_dim"],
        ).grid(row=0, column=3, padx=(0, 20), sticky="ne", pady=(14, 0)) # <- Movido para column=3

        ctk.CTkFrame(self, fg_color=C["red_dim"], height=1, corner_radius=0).grid(
            row=0, column=0, sticky="sew")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=C["panel"],
            segmented_button_fg_color=C["card"],
            segmented_button_selected_color=C["red_dim"],
            segmented_button_selected_hover_color=C["red"],
            segmented_button_unselected_color=C["card"],
            segmented_button_unselected_hover_color=C["border"],
            text_color=C["silver"],
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
        )
        self._tabs.grid(row=2, column=0, padx=14, pady=(10, 0), sticky="nsew")
        self._tabs.add("    OPERATION  ")
        self._tabs.add("    HISTORY  ")
        self._tabs.add("    CREDENTIALS  ")

        self._build_tab_op(self._tabs.tab("    OPERATION  "))
        self._build_tab_hist(self._tabs.tab("    HISTORY  "))
        self._build_tab_creds(self._tabs.tab("    CREDENTIALS  "))

    # ── Operation Tab ─────────────────────────────────────────────────────────
    def _build_tab_op(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(4, weight=1)

        # Target
        f1 = self._card(parent)
        f1.grid(row=0, column=0, sticky="ew", padx=2, pady=(6, 4))
        f1.grid_columnconfigure(1, weight=1)

        self._section_label(f1, "INVESTIGATION TARGET").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(f1, text="TARGET ›", font=ctk.CTkFont(family="Consolas", size=11),
                     text_color=C["silver_dim"], width=78).grid(
            row=1, column=0, padx=(14, 0), pady=(0, 12), sticky="w")

        self._entry_alvo = ctk.CTkEntry(
            f1, placeholder_text="Ex: RansomHub, CVE-2024-3094, LockBit, APT29...",
            height=38, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=C["bg"], border_color=C["red_dim"],
            text_color=C["white"], placeholder_text_color=C["silver_dim"])
        self._entry_alvo.grid(row=1, column=1, padx=(4, 14), pady=(0, 12), sticky="ew")
        self._entry_alvo.bind("<Return>", lambda e: self._iniciar_pipeline())
        self._entry_alvo.bind("<FocusIn>",  lambda e: self._entry_alvo.configure(border_color=C["red"]))
        self._entry_alvo.bind("<FocusOut>", lambda e: self._entry_alvo.configure(border_color=C["red_dim"]))

        # Options
        f2 = self._card(parent)
        f2.grid(row=1, column=0, sticky="ew", padx=2, pady=4)
        f2.grid_columnconfigure((0, 1), weight=1)

        self._section_label(f2, "PARAMETERS").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 6))

        self._check_force = ctk.CTkCheckBox(
            f2,
            text="Force new search  (ignore cache)",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["silver"],
            fg_color=C["red_dim"],
            hover_color=C["red"],
            checkmark_color=C["bg"],
            border_color=C["border_hi"],
        )
        self._check_force.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

        self._check_nvd = ctk.CTkCheckBox(
            f2,
            text="Include NVD/NIST validation",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["silver"],
            fg_color=C["red_dim"],
            hover_color=C["red"],
            checkmark_color=C["bg"],
            border_color=C["border_hi"],
        )
        self._check_nvd.grid(row=1, column=1, padx=14, pady=(0, 12), sticky="w")
        self._check_nvd.select()

        # Phase tracker
        self._tracker = PhaseTracker(parent)
        self._tracker.grid(row=2, column=0, sticky="ew", padx=2, pady=4)

        # Run button
        self._btn_run = ctk.CTkButton(
            parent, text="START INVESTIGATION", height=46,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color=C["red"], hover_color=C["red_hover"],
            text_color=C["white"], corner_radius=8,
            command=self._iniciar_pipeline)
        self._btn_run.grid(row=3, column=0, sticky="ew", padx=2, pady=4)

        # Console
        f3 = self._card(parent)
        f3.grid(row=4, column=0, sticky="nsew", padx=2, pady=(4, 2))
        f3.grid_columnconfigure(0, weight=1)
        f3.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(f3, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        hdr.grid_columnconfigure(1, weight=1)

        self._section_label(hdr, "// OPERATIONS CONSOLE").grid(row=0, column=0, sticky="w")

        self._lbl_timer = ctk.CTkLabel(hdr, text="",
                                       font=ctk.CTkFont(family="Consolas", size=10),
                                       text_color=C["silver_dim"])
        self._lbl_timer.grid(row=0, column=1, sticky="w", padx=10)

        self._lbl_tokens = ctk.CTkLabel(hdr, text="",
                                        font=ctk.CTkFont(family="Consolas", size=10),
                                        text_color=C["silver_dim"])
        self._lbl_tokens.grid(row=0, column=2, sticky="e", padx=(0, 8))

        self._btn_pdf = ctk.CTkButton(
            hdr, text="Open PDF", width=100, height=26,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=C["green_dim"], hover_color="#0d2418",
            text_color=C["green"], corner_radius=4,
            border_width=1, border_color=C["green"],
            state="disabled", command=self._abrir_pdf)
        self._btn_pdf.grid(row=0, column=3, sticky="e")

        self._console = ctk.CTkTextbox(
            f3, fg_color=C["console_bg"],
            text_color=C["console_red"],
            font=ctk.CTkFont(family="Consolas", size=11),
            border_color=C["border"], border_width=1,
            corner_radius=6, state="disabled", wrap="word")
        self._console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        for tag, fg in [
            ("accent", C["red"]),
            ("error",  C["red_hover"]),
            ("warn",   C["amber"]),
            ("ok",     C["green"]),
            ("dim",    C["console_dim"]),
            ("phase",  C["silver"]),
            ("white",  C["console_white"]),
        ]:
            self._console.tag_config(tag, foreground=fg)

        self._progress = ctk.CTkProgressBar(
            parent, fg_color=C["card"], progress_color=C["red"],
            height=3, corner_radius=2)
        self._progress.grid(row=5, column=0, sticky="ew", padx=2, pady=(0, 2))
        self._progress.set(0)

    # ── History Tab ───────────────────────────────────────────────────────────
    def _build_tab_hist(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        tb = ctk.CTkFrame(parent, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", padx=2, pady=(6, 4))
        tb.grid_columnconfigure(0, weight=1)

        self._section_label(tb, "REPORTS IN SQLite CACHE").grid(row=0, column=0, sticky="w")

        ctk.CTkButton(tb, text="↻  Refresh", width=96, height=26,
                      font=ctk.CTkFont(family="Consolas", size=11),
                      fg_color=C["card"], hover_color=C["border"],
                      text_color=C["silver"], corner_radius=6,
                      border_width=1, border_color=C["border"],
                      command=self._load_history).grid(row=0, column=1, padx=(8, 0))

        self._hist_frame = ctk.CTkScrollableFrame(
            parent, fg_color=C["card"], corner_radius=8,
            border_color=C["border"], border_width=1,
            scrollbar_button_color=C["border_hi"],
            scrollbar_button_hover_color=C["red_dim"])
        self._hist_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))
        self._hist_frame.grid_columnconfigure(0, weight=1)

        self._load_history()

    # ── Credentials Tab ───────────────────────────────────────────────────────
    def _build_tab_creds(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        self._section_label(parent, "API CREDENTIALS").grid(
            row=0, column=0, sticky="w", padx=2, pady=(10, 6))

        frame = self._card(parent)
        frame.grid(row=1, column=0, sticky="ew", padx=2)
        frame.grid_columnconfigure(1, weight=1)

        campos = [
            ("GEMINI_API_KEY", "Gemini API Key  *",
             "Required — Google AI Studio (aistudio.google.com)"),
            ("NVD_API_KEY", "NVD API Key",
             "Optional — NIST NVD · 50 req/30s with key"),
        ]
        self._entries_creds: "dict[str, ctk.CTkEntry]" = {}

        for i, (env_key, label, hint) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=C["silver"], width=160, anchor="e").grid(
                row=i * 2, column=0, padx=(16, 8), pady=(16, 2), sticky="e")

            entry = ctk.CTkEntry(frame, show="●", placeholder_text=hint,
                                 height=34, font=ctk.CTkFont(family="Consolas", size=12),
                                 fg_color=C["bg"], border_color=C["red_dim"],
                                 text_color=C["white"], placeholder_text_color=C["silver_dim"])
            entry.grid(row=i * 2, column=1, padx=(0, 16), pady=(16, 2), sticky="ew")
            entry.bind("<FocusIn>",  lambda e, en=entry: en.configure(border_color=C["red"]))
            entry.bind("<FocusOut>", lambda e, en=entry: en.configure(border_color=C["red_dim"]))
            self._entries_creds[env_key] = entry

            ctk.CTkLabel(frame, text=hint,
                         font=ctk.CTkFont(family="Consolas", size=9),
                         text_color=C["silver_dim"]).grid(
                row=i * 2 + 1, column=1, padx=(0, 16), pady=(0, 4), sticky="w")

            val = os.getenv(env_key, "")
            if val:
                entry.insert(0, val)

        ctk.CTkButton(parent, text="💾  Save to .env", height=38,
                      font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                      fg_color=C["red"], hover_color=C["red_hover"],
                      text_color=C["white"], corner_radius=8,
                      command=self._save_creds_manual).grid(
            row=2, column=0, sticky="ew", padx=2, pady=12)

        ctk.CTkLabel(parent,
                     text="⚠  Keys stored as plain text in .env — do not share this file.",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=C["amber"]).grid(row=3, column=0, padx=2, sticky="w")

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=26)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(bar, fg_color=C["red"], width=2, corner_radius=0).grid(
            row=0, column=0, sticky="ns", padx=(0, 10))

        self._lbl_status = ctk.CTkLabel(bar, text="●  READY",
                                        font=ctk.CTkFont(family="Consolas", size=10),
                                        text_color=C["green"])
        self._lbl_status.grid(row=0, column=1, padx=4, sticky="w")

        self._lbl_cache = ctk.CTkLabel(bar, text="",
                                       font=ctk.CTkFont(family="Consolas", size=10),
                                       text_color=C["silver_dim"])
        self._lbl_cache.grid(row=0, column=2, padx=14, sticky="e")

        self._update_cache_label()

    # ─────────────────────────────────────────────────────────────────────────
    # Visual helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _card(self, parent) -> ctk.CTkFrame:
        return ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=8,
                            border_color=C["border"], border_width=1)

    def _section_label(self, parent, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(parent, text=text,
                            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
                            text_color=C["red"])

    # ─────────────────────────────────────────────────────────────────────────
    # Thread-safe UI updates
    # ─────────────────────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        def _w():
            self._console.configure(state="normal")
            self._console.insert("end", f"[{ts}] ", "dim")
            self._console.insert("end", f"{msg}\n", tag or "")
            self._console.see("end")
            self._console.configure(state="disabled")
        self.after(0, _w)

    def _set_status(self, text: str, color: str):
        self.after(0, lambda: self._lbl_status.configure(text=text, text_color=C[color]))

    def _set_progress(self, value: float):
        def _u():
            if value < 0:
                self._progress.configure(mode="indeterminate")
                self._progress.start()
            else:
                self._progress.configure(mode="determinate")
                self._progress.stop()
                self._progress.set(value)
        self.after(0, _u)

    def _set_fase(self, idx: int):
        self._fase_atual = idx
        self.after(0, lambda: self._tracker.set_active(idx))

    def _done_fase(self, idx: int):
        self.after(0, lambda: self._tracker.set_done(idx))

    def _err_fase(self, idx: int):
        self.after(0, lambda: self._tracker.set_error(idx))

    # ─────────────────────────────────────────────────────────────────────────
    # Phase callback — chamado pelo ai_engine durante a execução do pipeline
    # ─────────────────────────────────────────────────────────────────────────
    def _phase_cb(self, idx: int, done: bool) -> None:
        """
        Recebe eventos de fase do pipeline assíncrono (rodando em outra thread).
        Todos os updates de UI passam pelo after() para garantir thread-safety.

        idx:  0=COLLECT, 1=RECON, 2=ANALYTICS, 3=STRATEGY
        done: False → fase iniciada | True → fase concluída
        """
        if done:
            self._done_fase(idx)
            if 0 <= idx < len(_FASE_LOG_DONE):
                self._log(_FASE_LOG_DONE[idx], "ok")
            if 0 <= idx < len(_FASE_PROGRESS):
                self._set_progress(_FASE_PROGRESS[idx])
        else:
            self._set_fase(idx)
            
            if 0 <= idx < len(_FASE_STATUS):
                label, color = _FASE_STATUS[idx]
                self._set_status(label, color)
            if idx > 0 and 0 <= idx < len(_FASE_LOG_START):
                self._log(_FASE_LOG_START[idx], "phase")

    # ── Timer ─────────────────────────────────────────────────────────────────
    def _timer_start(self):
        self._t_inicio = time.time()
        self._timer_tick()

    def _timer_stop(self):
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    def _timer_tick(self):
        if not self._running:
            return
        d   = int(time.time() - self._t_inicio)
        
        eta = sum(t for _, _, t in FASES[max(self._fase_atual, 0):])
        eta_s = f"  ETA ~{_fmt_seconds(eta)}" if eta else ""
        self._lbl_timer.configure(text=f"⏱ {_fmt_seconds(d)}{eta_s}",
                                  text_color=C["amber"])
        self._timer_job = self.after(1000, self._timer_tick)

    def _timer_finish(self, d: int):
        self._lbl_timer.configure(text=f"⏱ {_fmt_seconds(d)}",
                                  text_color=C["silver_dim"])

    # ── History ───────────────────────────────────────────────────────────────
    def _load_history(self):
        for w in self._hist_frame.winfo_children():
            w.destroy()
        try:
            reports = ReportCache().list_reports(limit=30)
        except Exception:
            reports = []

        if not reports:
            ctk.CTkLabel(self._hist_frame,
                         text="No reports yet. Run an investigation first.",
                         font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=C["silver_dim"]).grid(row=0, column=0, pady=40)
            return

        for i, r in enumerate(reports):
            self._report_card(r, i)
        self._update_cache_label(len(reports))

    def _report_card(self, r: dict, row: int):
        card = ctk.CTkFrame(self._hist_frame, fg_color=C["bg"], corner_radius=4,
                            border_color=C["border"], border_width=1)
        card.grid(row=row, column=0, sticky="ew", padx=6, pady=3)
        card.grid_columnconfigure(1, weight=1)

        pct = r.get("top_vector_pct")
        cor = _severity_color(pct)
        pct_s = f"{pct:.0f}%" if pct else "N/A"

        badge = ctk.CTkFrame(card, fg_color=C["red_glow"], corner_radius=4, width=60)
        badge.grid(row=0, column=0, rowspan=2, padx=10, pady=8, sticky="ns")
        badge.grid_propagate(False)

        ctk.CTkLabel(badge, text=pct_s,
                     font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                     text_color=cor).place(relx=0.5, rely=0.38, anchor="center")
        ctk.CTkLabel(badge, text="risk",
                     font=ctk.CTkFont(family="Consolas", size=7),
                     text_color=C["silver_dim"]).place(relx=0.5, rely=0.72, anchor="center")

        term  = r.get("search_term", "").upper()
        data  = r.get("created_at", "")[:10]
        hora  = r.get("created_at", "")[11:16]
        posts = r.get("post_count", 0)
        vetor = (r.get("top_vector") or "N/A")[:50]

        ctk.CTkLabel(card, text=f"[{r['id']:03d}]  {term}",
                     font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                     text_color=C["white"], anchor="w").grid(
            row=0, column=1, sticky="w", pady=(8, 0))

        ctk.CTkLabel(card,
                     text=f"{data} {hora}  ·  {posts} threads  ·  {vetor}",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=C["silver_dim"], anchor="w").grid(
            row=1, column=1, sticky="w", pady=(0, 8))

        ctk.CTkButton(card, text="PDF", width=58, height=28,
                      font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                      fg_color=C["red_glow"], hover_color=C["red_dim"],
                      text_color=C["red"], corner_radius=4,
                      border_width=1, border_color=C["red_dim"],
                      command=lambda rid=r["id"], st=r["search_term"]:
                          self._reexport(rid, st)).grid(
            row=0, column=2, rowspan=2, padx=10, pady=8)

    # ── Re-export ─────────────────────────────────────────────────────────────
    def _reexport(self, report_id: int, search_term: str):
        if self._running:
            messagebox.showwarning("Running", "Wait for the current operation to finish.")
            return
        threading.Thread(target=self._worker_reexport,
                         args=(report_id, search_term), daemon=True).start()

    def _worker_reexport(self, report_id: int, search_term: str):
        self._tabs.set("    OPERATION  ")
        self._log(f"Re-exporting ID={report_id:03d} · '{search_term}'...", "accent")
        self._set_status("●  RE-EXPORTING...", "amber")
        self._set_progress(-1)

        safe = search_term.replace(" ", "_").replace("/", "-")
        out_dir = cfg.base_dir / "historico" / "reexports"
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp_md  = out_dir / f"_tmp_{report_id}.md"
        dst_pdf = out_dir / f"Dossier_{safe}_ID{report_id:03d}.pdf"

        try:
            report = ReportCache().get_by_id(report_id)
            if not report:
                self._log(f"Report ID={report_id} not found.", "error")
                self._set_status("●  ERROR", "red_hover")
                return

            with open(tmp_md, "w", encoding="utf-8") as f:
                f.write(report["report_md"])

            ok = generate_pdf_report(str(tmp_md), report["telemetry"], str(dst_pdf))
            try:
                tmp_md.unlink()
            except Exception:
                pass

            if ok:
                self._ultimo_pdf = dst_pdf
                self._log(f"PDF saved: {dst_pdf}", "ok")
                self._set_status("●  PDF READY", "green")
                self.after(0, lambda: self._btn_pdf.configure(state="normal"))
                self._set_progress(1.0)
                self.after(0, lambda: messagebox.showinfo(
                    "Re-exported", f"Dossier ID={report_id} saved to:\n{dst_pdf}"))
            else:
                self._log("PDF generation failed.", "error")
                self._set_status("●  PDF ERROR", "red_hover")
                self._set_progress(0)

        except Exception as e:
            self._log(f"Error: {e}", "error")
            self._set_status("●  ERROR", "red_hover")
            self._set_progress(0)

    # ── Main Pipeline ─────────────────────────────────────────────────────────
    def _iniciar_pipeline(self):
        if self._running:
            return

        gemini_e = self._entries_creds.get("GEMINI_API_KEY")
        gemini_v = (gemini_e.get().strip() if gemini_e else "") or os.getenv("GEMINI_API_KEY", "")

        if not gemini_v:
            messagebox.showwarning("Missing Key",
                                   "Gemini API Key required.\nConfigure in CREDENTIALS tab.")
            return

        alvo = self._entry_alvo.get().strip()
        if not alvo:
            messagebox.showwarning("No Target", "Enter a target to investigate.")
            return

        force = bool(self._check_force.get())
        include_nvd = bool(self._check_nvd.get())
        self._save_creds_auto()

        self._running    = True
        self._fase_atual = -1
        self._ultimo_pdf = None
        self._include_nvd = include_nvd

        self.after(0, lambda: self._tracker.set_collect_mode(include_nvd))
        self.after(0, lambda: self._tracker.reset())
        self.after(0, lambda: self._btn_run.configure(
            state="disabled", text="⏳  RUNNING...",
            fg_color=C["red_bg"], text_color=C["red"]))
        self.after(0, lambda: self._btn_pdf.configure(state="disabled"))
        self.after(0, lambda: self._lbl_tokens.configure(text=""))
        self.after(0, lambda: self._console.configure(state="normal"))
        self.after(0, lambda: self._console.delete("0.0", "end"))
        self.after(0, lambda: self._console.configure(state="disabled"))
        self.after(0, self._timer_start)

        threading.Thread(
            target=self._worker,
            args=(alvo, force, include_nvd),
            daemon=True,
        ).start()

    def _worker(self, alvo: str, force: bool, include_nvd: bool):
        t0 = time.time()
        self._log("─" * 50, "dim")
        self._log(f"KojiX  ·  TARGET: {alvo.upper()}", "accent")
        self._log("─" * 50, "dim")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Fase 0 (COLLECT) — ativa manualmente aqui antes do callback
            self._set_fase(0)
            self._set_status("●  COLLECTING...", "amber")
            self._set_progress(-1)
            if include_nvd:
                self._log("Collecting Reddit + NVD/NIST in parallel...", "phase")
            else:
                self._log("Collecting Reddit OSINT only (NVD disabled)...", "phase")

            sucesso, probabilidades = loop.run_until_complete(
                analyze_threat_data(
                    search_term=alvo,
                    output_filepath=str(cfg.report_md),
                    force_refresh=force,
                    include_nvd=include_nvd,
                    phase_callback=self._phase_cb,  # ← atualização em tempo real
                )
            )

            if not sucesso:
                self._err_fase(self._fase_atual)
                self._log("FAILED: Check API quota or network.", "error")
                self._set_status("●  FAILED", "red_hover")
                return

            # Fase 4 (REPORT/PDF) — controlada aqui na GUI
            self._set_fase(4)
            self._set_status("●  GENERATING PDF...", "amber")
            self._log("Compiling PDF...", "phase")
            self._set_progress(0.9)

            sucesso_pdf = generate_pdf_report(
                md_filepath=str(cfg.report_md),
                probabilidades=probabilidades,
                pdf_filepath=str(cfg.report_pdf),
            )

            decorrido = int(time.time() - t0)
            self._timer_stop()

            if sucesso_pdf:
                self._done_fase(4)
                self._set_progress(1.0)

                pdf_arquivado = _arquivar_sessao(alvo)
                if pdf_arquivado and pdf_arquivado.exists():
                    self._ultimo_pdf = pdf_arquivado
                    self._log(f"Archived: {pdf_arquivado}", "ok")
                else:
                    self._ultimo_pdf = cfg.report_pdf

                self.after(0, lambda: self._lbl_tokens.configure(
                    text=f"~{(TOKEN_EST_INPUT + TOKEN_EST_OUTPUT) // 1000}k tokens",
                    text_color=C["silver_dim"]))
                self.after(0, lambda: self._timer_finish(decorrido))

                self._log("─" * 50, "dim")
                self._log(f"COMPLETE · {_fmt_seconds(decorrido)}", "ok")

                if probabilidades:
                    top = next(iter(probabilidades))
                    pct = probabilidades[top]
                    tag = "error" if pct >= 60 else "warn" if pct >= 35 else "ok"
                    self._log(f"Dominant vector: {top} ({pct:.1f}%)", tag)

                self._log("─" * 50, "dim")
                self._set_status("●  DOSSIER READY", "green")
                self.after(0, lambda: self._btn_pdf.configure(state="normal"))
                self.after(0, self._load_history)
                self.after(0, self._update_cache_label)
                self.after(0, lambda: messagebox.showinfo(
                    "Complete",
                    f"Dossier on '{alvo}' generated.\n"
                    f"Time: {_fmt_seconds(decorrido)}\n\n"
                    "Click 'Open PDF' to view."))
            else:
                self._err_fase(4)
                self._log("PDF failed. Markdown at: data/report_output.md", "warn")
                self._set_status("●  PDF ERROR", "red_hover")

        except Exception as e:
            self._log(f"CRITICAL: {e}", "error")
            self._set_status("●  ERROR", "red_hover")

        finally:
            loop.close()
            self._running = False
            self._timer_stop()
            self.after(0, lambda: self._btn_run.configure(
                state="normal", text="START INVESTIGATION",
                fg_color=C["red"], text_color=C["white"]))

    # ── Credentials ───────────────────────────────────────────────────────────
    def _save_creds_auto(self):
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        for k, e in self._entries_creds.items():
            v = e.get().strip()
            if v and v != os.getenv(k, ""):
                set_key(str(ENV_PATH), k, v)
                os.environ[k] = v

    def _save_creds_manual(self):
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        saved = []
        for k, e in self._entries_creds.items():
            v = e.get().strip()
            if v:
                set_key(str(ENV_PATH), k, v)
                os.environ[k] = v
                saved.append(k)
        if saved:
            messagebox.showinfo("Saved", "Saved to .env:\n" + "\n".join(saved))
        else:
            messagebox.showwarning("Nothing", "Fill in at least one API key.")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _abrir_pdf(self):
        if self._ultimo_pdf and self._ultimo_pdf.exists():
            _open_file(self._ultimo_pdf)
        else:
            messagebox.showwarning("Not Found", "PDF file not found.")

    def _update_cache_label(self, count: Optional[int] = None):
        def _u():
            try:
                n = count if count is not None else len(ReportCache().list_reports())
                self._lbl_cache.configure(text=f"cache: {n}  ·  {cfg.cache_db.name}")
            except Exception:
                pass
        self.after(0, _u)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = KojiXApp()
    app.mainloop()
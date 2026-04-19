#!/usr/bin/env python3
# launcher.py
"""
KojiX — Graphical Launcher v1.0.0

"""
import io
import os
import queue
import subprocess
import sys
import threading
import time
import asyncio
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import customtkinter as ctk
from dotenv import load_dotenv

load_dotenv(Path(".env"))
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ASSETS = Path("assets")

C = {
    "bg":           "#08080d",
    "panel":        "#0e0f16",
    "card":         "#12131b",
    "card_hover":   "#181922",
    "border":       "#202433",
    "border_hi":    "#31374a",
    "red":          "#8f1d27",
    "red_hover":    "#a82a35",
    "red_dim":      "#4d1117",
    "red_bg":       "#21090d",
    "white":        "#d8deea",
    "silver":       "#c3cede",
    "silver_dim":   "#667387",
    "silver_muted": "#323847",
    "green":        "#3ac97c",
    "green_dim":    "#0e2417",
    "amber":        "#c8942b",
    "console_bg":   "#06070b",
    "console_dim":  "#4e596b",
}


# ── Asset helpers ─────────────────────────────────────────────────────────────
def _load_logo(max_height=44):
    try:
        from PIL import Image
        img = Image.open(ASSETS / "logo.png").convert("RGBA")
        orig_w, orig_h = img.size
        ratio = max_height / orig_h
        target_w = max(1, int(orig_w * ratio))
        return ctk.CTkImage(img, size=(target_w, max_height))
    except Exception:
        return None


def _set_icon(window):
    ico = ASSETS / "icone.ico"
    if ico.exists():
        try:
            window.iconbitmap(str(ico))
        except Exception:
            pass


# ── stdout → queue ────────────────────────────────────────────────────────────
class _QueueWriter(io.TextIOBase):
    def __init__(self, q: queue.Queue, tag: str = ""):
        self._q, self._tag = q, tag

    def write(self, s: str) -> int:
        if s and s.strip():
            self._q.put((s.rstrip("\n"), self._tag))
        return len(s)

    def flush(self): pass


# =============================================================================
# Launcher
# =============================================================================
class KojiXLauncher(ctk.CTk):
    W_CHOICE  = 540
    H_CHOICE  = 480
    W_CONSOLE = 860
    H_CONSOLE = 660

    def __init__(self):
        super().__init__()
        self.title("KojiX — Launcher")
        self.geometry(f"{self.W_CHOICE}x{self.H_CHOICE}")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        _set_icon(self)

        self._q               = queue.Queue()
        self._cli_running     = False
        self._elapsed_running = False
        self._t0              = 0.0
        self._orig_stdout     = sys.stdout
        self._orig_stderr     = sys.stderr

        self._build_choice_screen()

    # =========================================================================
    # CHOICE SCREEN
    # =========================================================================
    def _build_choice_screen(self):
        self._choice_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._choice_frame.pack(fill="both", expand=True)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self._choice_frame, fg_color=C["panel"],
                           corner_radius=0, height=116)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        logo_img = _load_logo(max_height=220)
        if logo_img:
            ctk.CTkLabel(hdr, text="", image=logo_img).place(relx=0.5, rely=0.42, anchor="center")
            ctk.CTkLabel(
                hdr,
                text="Autonomous Cyber Threat Intelligence Engine",
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=C["silver_dim"],
            ).place(relx=0.5, rely=0.78, anchor="center")
        else:
            ctk.CTkLabel(
                hdr, text="KOJIX LAUNCHER",
                font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
                text_color=C["red"],
            ).place(relx=0.5, rely=0.40, anchor="center")
            ctk.CTkLabel(
                hdr,
                text="Autonomous Cyber Threat Intelligence Engine",
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=C["silver_dim"],
            ).place(relx=0.5, rely=0.74, anchor="center")

        ctk.CTkFrame(self._choice_frame, fg_color=C["red_dim"],
                     height=1, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            self._choice_frame,
            text="SELECT OPERATION MODE",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color=C["silver_muted"],
        ).pack(pady=(22, 14))

        # ── Cards ─────────────────────────────────────────────────────────────
        row = ctk.CTkFrame(self._choice_frame, fg_color="transparent")
        row.pack(padx=32, fill="x", expand=False)
        row.grid_columnconfigure((0, 1), weight=1)

        self._card_gui = self._make_card(
            row, col=0,
            title="GRAPHICAL\nINTERFACE",
            desc="Visual dashboard\nphase tracker\nintegrated history",
            badge="RECOMMENDED", badge_color=C["green"],
            cmd=self._launch_gui,
        )
        self._card_cli = self._make_card(
            row, col=1,
            title="CLI\nCONSOLE",
            desc="Embedded terminal\nreal-time pipeline\nhistory via button",
            badge="ADVANCED", badge_color=C["amber"],
            cmd=self._launch_cli_screen,
        )

        ctk.CTkLabel(
            self._choice_frame,
            text="v1.0.0  ·  KojiX Security",
            font=ctk.CTkFont(family="Consolas", size=8),
            text_color=C["silver_muted"],
        ).pack(side="bottom", pady=14)

    def _make_card(self, parent, col, title, desc, badge, badge_color, cmd):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=10,
                            border_color=C["border"], border_width=1,
                            cursor="hand2")
        card.grid(row=0, column=col, padx=10, pady=4, sticky="nsew")

        def _on_enter(e):
            card.configure(border_color=C["red"], fg_color=C["card_hover"])
        def _on_leave(e):
            card.configure(border_color=C["border"], fg_color=C["card"])
        def _on_click(e):
            cmd()

        def _bind_all(widget):
            widget.bind("<Enter>", _on_enter)
            widget.bind("<Leave>", _on_leave)
            widget.bind("<Button-1>", _on_click)
            for child in widget.winfo_children():
                _bind_all(child)

        inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        inner.pack(padx=18, pady=20, fill="both", expand=True)

        ctk.CTkLabel(inner, text=title,
                     font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
                     text_color=C["white"], justify="center",
                     cursor="hand2").pack()

        ctk.CTkLabel(inner, text=desc,
                     font=ctk.CTkFont(family="Consolas", size=12),
                     text_color=C["silver_dim"], justify="center",
                     cursor="hand2").pack(pady=(12, 0))

        badge_f = ctk.CTkFrame(inner, fg_color=C["red_bg"], corner_radius=4,
                               cursor="hand2")
        badge_f.pack(pady=(16, 0))

        ctk.CTkLabel(badge_f, text=badge,
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=badge_color, cursor="hand2").pack(padx=12, pady=5)

        btn = ctk.CTkButton(
            inner, text="SELECT", height=38,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color=C["red"], hover_color=C["red_hover"],
            text_color=C["white"], corner_radius=6,
            command=cmd,
        )
        btn.pack(fill="x", pady=(20, 0))

        self.after(50, lambda: _bind_all(card))
        return card

    # =========================================================================
    # GUI MODE
    # =========================================================================
    def _launch_gui(self):
        try:
            self.destroy()
            
            import gui
            
            app = gui.KojiXApp()
            app.mainloop()
            
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erro Crítico", f"Falha ao carregar a Interface Gráfica:\n{str(e)}")

    # =========================================================================
    # CLI MODE
    # =========================================================================
    def _launch_cli_screen(self):
        self._choice_frame.destroy()
        self.geometry(f"{self.W_CONSOLE}x{self.H_CONSOLE}")
        self.resizable(True, True)
        self._build_cli_screen()

    def _build_cli_screen(self):
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        # Note: The textbox is now in row 2, so row 2 expands
        root.grid_rowconfigure(2, weight=1)

        # ── Control Bar (Top) ─────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(root, fg_color=C["panel"], corner_radius=0)
        ctrl.grid(row=0, column=0, sticky="ew")
        ctrl.grid_columnconfigure(0, weight=1) 

        
        self._cli_entry = ctk.CTkEntry(
            ctrl,
            placeholder_text="Target: RansomHub, CVE-2024-3094, LockBit...",
            height=34,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=C["bg"], border_color=C["red_dim"],
            text_color=C["white"], placeholder_text_color=C["silver_dim"],
        )
        self._cli_entry.grid(row=0, column=0, padx=(14, 6), pady=16, sticky="ew")
        self._cli_entry.bind("<Return>", lambda e: self._cli_run())
        self._cli_entry.bind("<FocusIn>",
            lambda e: self._cli_entry.configure(border_color=C["red"]))
        self._cli_entry.bind("<FocusOut>",
            lambda e: self._cli_entry.configure(border_color=C["red_dim"]))

        self._chk_force = ctk.CTkCheckBox(
            ctrl, text="Force", width=72,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["silver"], fg_color=C["red_dim"],
            hover_color=C["red"], checkmark_color=C["bg"],
            border_color=C["border_hi"],
        )
        self._chk_force.grid(row=0, column=1, padx=4)

        self._chk_nvd = ctk.CTkCheckBox(
            ctrl, text="NVD", width=60,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["silver"], fg_color=C["red_dim"],
            hover_color=C["red"], checkmark_color=C["bg"],
            border_color=C["border_hi"],
        )
        self._chk_nvd.grid(row=0, column=2, padx=4)
        self._chk_nvd.select()

        self._btn_run = ctk.CTkButton(
            ctrl, text="▶ RUN", width=80, height=34,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=C["red"], hover_color=C["red_hover"],
            text_color=C["white"], corner_radius=5,
            command=self._cli_run,
        )
        self._btn_run.grid(row=0, column=3, padx=8)

        ctk.CTkButton(
            ctrl, text="HISTORY", width=90, height=34,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=C["card"], hover_color=C["border"],
            text_color=C["silver"], corner_radius=5,
            border_width=1, border_color=C["border_hi"],
            command=self._cli_list,
        ).grid(row=0, column=4, padx=4)

        self._lbl_status = ctk.CTkLabel(
            ctrl, text="● READY", width=100,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=C["green"],
        )
        self._lbl_status.grid(row=0, column=5, padx=(10, 14))

        # ── Console Header (Holds Logo and Info Text) ─────────────────────────
        console_hdr = ctk.CTkFrame(root, fg_color="transparent")
        console_hdr.grid(row=1, column=0, sticky="ew", padx=14, pady=(10, 0))
        console_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            console_hdr,
            text="KojiX CTI Console  ·  Enter a target and press ▶ RUN or Enter",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=C["red"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=10)

        self._btn_open_pdf = ctk.CTkButton(
            console_hdr, text="📄 Open PDF", height=28, width=110,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color=C["green_dim"], hover_color="#0d2418",
            text_color=C["green"], corner_radius=4,
            border_width=1, border_color=C["green"]
        )
        self._btn_open_pdf.grid(row=0, column=1, padx=(0, 20), sticky="e")
        self._btn_open_pdf.grid_remove()  

        logo_img = _load_logo(max_height=220)
        if logo_img:
            ctk.CTkLabel(console_hdr, text="", image=logo_img).grid(
                row=0, column=2, sticky="e"
            )

        # ── Console output ────────────────────────────────────────────────────
        self._cli_out = ctk.CTkTextbox(
            root,
            fg_color=C["console_bg"],
            text_color="#c2cedf",
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=0, corner_radius=0,
            state="disabled", wrap="word",
        )
        self._cli_out.grid(row=2, column=0, sticky="nsew") # Shifted to row 2

        for tag, color in [
            ("ok",    C["green"]),
            ("warn",  C["amber"]),
            ("err",   "#c0392b"),
            ("dim",   C["console_dim"]),
            ("head",  C["red"]),
            ("phase", C["silver"]),
        ]:
            self._cli_out.tag_config(tag, foreground=color)

        # ── Status bar (footer) ───────────────────────────────────────────────
        bar = ctk.CTkFrame(root, fg_color=C["panel"], corner_radius=0, height=24)
        bar.grid(row=3, column=0, sticky="ew") # Shifted to row 3
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(bar, fg_color=C["red"], width=2,
                     corner_radius=0).grid(row=0, column=0, sticky="ns")

        self._lbl_elapsed = ctk.CTkLabel(
            bar, text="",
            font=ctk.CTkFont(family="Consolas", size=8),
            text_color=C["silver_dim"],
        )
        self._lbl_elapsed.grid(row=0, column=1, padx=10, sticky="w")

        ctk.CTkButton(
            bar, text="← MENU", width=70, height=18,
            font=ctk.CTkFont(family="Consolas", size=8),
            fg_color="transparent", hover_color=C["border"],
            text_color=C["silver_dim"], corner_radius=3,
            command=self._voltar_menu,
        ).grid(row=0, column=2, padx=10, sticky="e")

        self._poll_queue()

    # ─────────────────────────────────────────────────────────────────────────
    def _voltar_menu(self):
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        for w in self.winfo_children():
            w.destroy()
        self.geometry(f"{self.W_CHOICE}x{self.H_CHOICE}")
        self.resizable(False, False)
        self._build_choice_screen()

    # ── Console helpers ───────────────────────────────────────────────────────
    def _cprint(self, msg: str, tag: str = ""):
        self._cli_out.configure(state="normal")
        self._cli_out.insert("end", msg + "\n", tag or "")
        self._cli_out.see("end")
        self._cli_out.configure(state="disabled")

    def _auto_tag(self, msg: str) -> str:
        low = msg.lower()
        if any(x in low for x in ("erro", "error", "critical", "falhou", "failed")):
            return "err"
        if any(x in low for x in ("[ok]", "✓", "concluí", "gerado", "sucesso", "success")):
            return "ok"
        if any(x in low for x in ("warn", "aviso", "[warn", "warning")):
            return "warn"
        if msg.strip().startswith("  ["):
            return "phase"
        if msg.startswith("─") or msg.strip().startswith("─"):
            return "dim"
        return ""

    def _poll_queue(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                self._cprint(msg, tag or self._auto_tag(msg))
        except queue.Empty:
            pass
        if hasattr(self, "_cli_out"):
            self.after(100, self._poll_queue)

    def _set_status(self, text: str, color: str):
        self.after(0, lambda: self._lbl_status.configure(text=text, text_color=color))

    # ── Pipeline ──────────────────────────────────────────────────────────────
    def _cli_run(self):
        alvo = self._cli_entry.get().strip()
        if not alvo:
            self._cprint("  [ERROR] Enter a target.", "err")
            return
        if self._cli_running:
            self._cprint("  [WARNING] Wait for the pipeline to finish.", "warn")
            return

        self._cli_running = True
        self._t0 = time.time()
        self._btn_run.configure(state="disabled", text="⏳")
        self._btn_open_pdf.grid_remove()
        self._set_status("● RUNNING...", C["amber"])
        self._start_timer()

        sys.stdout = _QueueWriter(self._q)
        sys.stderr = _QueueWriter(self._q, "err")

        threading.Thread(
            target=self._worker,
            args=(alvo, bool(self._chk_force.get()), bool(self._chk_nvd.get())),
            daemon=True,
        ).start()

    def _worker(self, alvo: str, force: bool, include_nvd: bool):
        import asyncio, logging

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("  %(levelname)-7s %(message)s"))
        root_log = logging.getLogger()
        orig_lvl = root_log.level
        root_log.addHandler(handler)
        root_log.setLevel(logging.INFO)

        try:
            from core.ai_engine import analyze_threat_data
            from core.config import DEFAULT_CONFIG as cfg
            from core.exporter import generate_pdf_report

            sep = "─" * 68
            print(f"\n{sep}")
            print(f"  TARGET: {alvo.upper()}  |  NVD: {'on' if include_nvd else 'off'}  |  force: {force}")
            print(f"{sep}\n")

            def _phase(idx: int, done: bool):
                nomes  = ["COLLECT", "RECON", "ANALYTICS", "STRATEGY"]
                nome   = nomes[idx] if idx < len(nomes) else f"PHASE-{idx}"
                print(f"  [{nome}] {'done ✓' if done else 'started...'}")

            ok, probs = asyncio.run(
                analyze_threat_data(
                    search_term=alvo,
                    output_filepath=str(cfg.report_md),
                    force_refresh=force,
                    include_nvd=include_nvd,
                    phase_callback=_phase,
                )
            )

            if not ok:
                print("\n  [ERROR] Pipeline failed. Check GEMINI_API_KEY.")
                self._set_status("● ERROR", "#c0392b")
                return

            print("\n  [REPORT] Generating PDF...")
            ok_pdf = generate_pdf_report(
                md_filepath=str(cfg.report_md),
                probabilidades=probs,
                pdf_filepath=str(cfg.report_pdf),
            )

            elapsed = int(time.time() - self._t0)
            m, s = divmod(elapsed, 60)
            tempo = f"{m}m{s:02d}s" if m else f"{s}s"

            if ok_pdf:
                print(f"\n  [OK] PDF: {cfg.report_pdf}  ({tempo})")
                self._set_status("● OK", C["green"])
                self.after(300, lambda: self._add_open_btn(cfg.report_pdf))
            else:
                print(f"  [WARNING] PDF failed. MD: {cfg.report_md}")
                self._set_status("● WARNING", C["amber"])

            if probs:
                print(f"\n  Telemetry:")
                for v, p in probs.items():
                    bar = "█" * max(1, int(p / 4))
                    print(f"    {v:<40} {p:>5.1f}%  {bar}")

            print(f"\n{sep}\n")

        except Exception as e:
            print(f"\n  [CRITICAL] {e}")
            self._set_status("● CRITICAL", "#c0392b")

        finally:
            root_log.removeHandler(handler)
            root_log.setLevel(orig_lvl)
            sys.stdout = self._orig_stdout
            sys.stderr = self._orig_stderr
            self._cli_running = False
            self._stop_timer()
            self.after(0, lambda: self._btn_run.configure(
                state="normal", text="▶ RUN"))

    def _add_open_btn(self, pdf_path):
        def _open():
            try:
                if sys.platform == "win32":
                    os.startfile(str(pdf_path))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(pdf_path)])
                else:
                    subprocess.run(["xdg-open", str(pdf_path)])
            except Exception:
                pass

        
        self._btn_open_pdf.configure(command=_open)
        self._btn_open_pdf.grid()

    # ── History ─────────────────────────────────────────────────────────────
    def _cli_list(self):
        try:
            from core.cache import ReportCache
            reports = ReportCache().list_reports(limit=30)
        except Exception as e:
            self._cprint(f"  [ERROR] {e}", "err")
            return

        sep = "─" * 68
        self._cprint(f"\n{sep}", "dim")
        self._cprint("  HISTORY  ·  last 30 reports", "head")
        self._cprint(sep, "dim")
        if not reports:
            self._cprint("  No reports in cache.", "warn")
        else:
            self._cprint(f"  {'ID':>4}  {'Target':<26}  {'Date':>10}  {'Posts':>5}  Risk", "phase")
            self._cprint("  " + "·" * 60, "dim")
            for r in reports:
                pct = r.get("top_vector_pct")
                self._cprint(
                    f"  {r['id']:>4}  {r['search_term']:<26}  "
                    f"{r['created_at'][:10]:>10}  {r['post_count']:>5}  "
                    f"{f'{pct:.0f}%' if pct else 'N/A'}"
                )
        self._cprint(f"{sep}\n", "dim")

    # ── Timer ─────────────────────────────────────────────────────────────────
    def _start_timer(self):
        self._elapsed_running = True
        self._tick()

    def _stop_timer(self):
        self._elapsed_running = False
        self.after(0, lambda: self._lbl_elapsed.configure(text=""))

    def _tick(self):
        if not self._elapsed_running:
            return
        d = int(time.time() - self._t0)
        m, s = divmod(d, 60)
        self._lbl_elapsed.configure(
            text=f"⏱ {m}m{s:02d}s" if m else f"⏱ {s}s",
            text_color=C["amber"],
        )
        self.after(1000, self._tick)


# =============================================================================
def main():
    KojiXLauncher().mainloop()


if __name__ == "__main__":
    main()
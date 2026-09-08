# =============================================================================
#  Anime & Video Tracker  v2.3
#  Portable Windows · File Lock Detection · Themes · List + Card Views
#  Thumbnails via Windows Shell IShellItemImageFactory (pure ctypes)
#  Dependencias: solo stdlib Python (tkinter, ctypes, json, os, re, sys)
# =============================================================================

import os, re, json, sys, ctypes, base64, queue, threading, struct, time
try:
    import cv2  # type: ignore
except ImportError:
    pass
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk

# ---------------------------------------------------------------------------
#  CONSTANTS
# ---------------------------------------------------------------------------
APP_TITLE   = "Anime & Video Tracker"
APP_VERSION = "2.3"

SYNC_INTERVAL_S = 0.5   # segundos entre chequeos del watcher de ventanas

EXTS_VALIDAS     = {".mp4",".mkv",".avi",".mov",".webm",".flv",".wmv",".m4v",".ts",".ogv"}
ARCHIVO_REGISTRO = ".tracker.json"
ARCHIVO_SETTINGS = "tracker_settings.json"
FUENTES          = [
    "Consolas", "Courier New", "JetBrains Mono", "Comic Sans MS", 
    "Segoe UI", "Calibri", "Verdana", "Arial", "Tahoma", "Trebuchet MS", "Monospace"
]

GENERIC_READ                      = 0x80000000
OPEN_EXISTING                     = 3
FILE_ATTRIBUTE_NORMAL             = 0x80
INVALID_HANDLE_VALUE              = ctypes.c_void_p(-1).value
ERROR_SHARING_VIOLATION           = 32
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

THUMB_W, THUMB_H = 200, 112   # 16:9 thumbnail size

# IID_IShellItemImageFactory {bcc18b79-ba16-442f-80c4-8a59c30c4630}
_IID_SIIF = (ctypes.c_ubyte * 16)(
    0x79,0x8b,0xc1,0xbc, 0x16,0xba, 0x2f,0x44,
    0x80,0xc4,0x8a,0x59,0xc3,0x0c,0x46,0x30
)

# ---------------------------------------------------------------------------
#  THEMES
# ---------------------------------------------------------------------------
TEMA_OSCURO = {
    "bg_root":"#000000",       "bg_header":"#0a0a0a",
    "bg_list":"#000000",       "bg_row_normal":"#000000",
    "bg_row_alt":"#0a0a0a",    "bg_row_active":"#2E0B0E",
    "bg_row_last":"#1A1200",   "bg_row_hover":"#111111",
    "bg_scrollbar":"#0a0a0a",  "bg_footer":"#050505",
    "bg_btn":"#111111",        "bg_btn_hover":"#222222",
    "bg_card":"#0a0a0a",       "bg_card_hover":"#111111",
    "bg_card_active":"#2E0B0E","bg_card_last":"#1A1200",
    "fg_title":"#ffffff",      "fg_sub":"#aaaaaa",
    "fg_normal":"#ffffff",     "fg_active":"#DC143C",
    "fg_last":"#FFB703",       "fg_btn":"#ffffff",
    "badge_mpc":"#DC143C",     "badge_vlc":"#DC143C",
    "badge_pot":"#DC143C",     "badge_other":"#DC143C",
    "border":"#222222",        "border_active":"#DC143C",
    "border_card":"#222222",   "separator":"#222222",
    "tooltip_bg":"#111111",    "tooltip_fg":"#ffffff",
    "thumb_bg":"#000000",      "thumb_icon":"#555555",
    "thumb_play":"#DC143C",    "focus_border":"#DC143C",
}
TEMA_CLARO = {
    "bg_root":"#ffffff",       "bg_header":"#f2f2f2",
    "bg_list":"#ffffff",       "bg_row_normal":"#ffffff",
    "bg_row_alt":"#f2f2f2",    "bg_row_active":"#FADBDD",
    "bg_row_last":"#FFF2D6",   "bg_row_hover":"#f9f9f9",
    "bg_scrollbar":"#f2f2f2",  "bg_footer":"#f2f2f2",
    "bg_btn":"#e6e6e6",        "bg_btn_hover":"#cccccc",
    "bg_card":"#ffffff",       "bg_card_hover":"#f9f9f9",
    "bg_card_active":"#FADBDD","bg_card_last":"#FFF2D6",
    "fg_title":"#000000",      "fg_sub":"#555555",
    "fg_normal":"#000000",     "fg_active":"#D62828",
    "fg_last":"#D18E00",       "fg_btn":"#000000",
    "badge_mpc":"#D62828",     "badge_vlc":"#D62828",
    "badge_pot":"#D62828",     "badge_other":"#D62828",
    "border":"#cccccc",        "border_active":"#DC143C",
    "border_card":"#cccccc",   "separator":"#cccccc",
    "tooltip_bg":"#f2f2f2",    "tooltip_fg":"#000000",
    "thumb_bg":"#ffffff",      "thumb_icon":"#aaaaaa",
    "thumb_play":"#DC143C",    "focus_border":"#DC143C",
}
C = dict(TEMA_OSCURO)   # active theme dict — mutated on theme change

# ---------------------------------------------------------------------------
#  PLAYER MAP
# ---------------------------------------------------------------------------
REPRODUCTORES_MAPA = {
    "mpc-hc.exe":"CODEC MPC","mpc-hc64.exe":"CODEC MPC",
    "mpc-be.exe":"CODEC MPC","mpc-be64.exe":"CODEC MPC",
    "mpc.exe":"CODEC MPC","mediaplayerclassic.exe":"CODEC MPC",
    "k-lite.exe":"CODEC MPC","vlc.exe":"VLC",
    "potplayer.exe":"POTPLAYER","potplayer64.exe":"POTPLAYER",
    "potplayermini.exe":"POTPLAYER","potplayermini64.exe":"POTPLAYER",
    "daum.potplayer.exe":"POTPLAYER","mpv.exe":"MPV",
    "wmplayer.exe":"WINDOWS MEDIA",
    "microsoft.media.player.exe":"PELICULAS Y TV","video.ui.exe":"PELICULAS Y TV",
    "kmplayer.exe":"KMPLAYER","gom.exe":"GOM PLAYER",
    "gomplayerfree.exe":"GOM PLAYER","bsplayer.exe":"BS.PLAYER",
    "smplayer.exe":"SMPLAYER","chrome.exe":"CHROME",
    "firefox.exe":"FIREFOX","msedge.exe":"EDGE",
}

# ---------------------------------------------------------------------------
#  WIN32 SETUP
# ---------------------------------------------------------------------------
try:
    _k32  = ctypes.windll.kernel32
    _u32  = ctypes.windll.user32
    _sh32 = ctypes.windll.shell32
    _gdi  = ctypes.windll.gdi32
    _ole  = ctypes.windll.ole32
    _WIN32_OK = True
except AttributeError:
    _WIN32_OK = False

_EnumCB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


# ---------------------------------------------------------------------------
#  FILE LOCK DETECTION
# ---------------------------------------------------------------------------
def esta_archivo_en_uso(ruta):
    if not _WIN32_OK:
        return False
    try:
        h = _k32.CreateFileW(ruta, GENERIC_READ, 0, None,
                             OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
        if h == INVALID_HANDLE_VALUE:
            return _k32.GetLastError() == ERROR_SHARING_VIOLATION
        _k32.CloseHandle(h)
        return False
    except Exception:
        return False


def obtener_nombre_reproductor(archivo_nombre):
    if not _WIN32_OK:
        return "REPRODUCTOR"
    base  = os.path.splitext(archivo_nombre)[0].lower()
    namel = archivo_nombre.lower()
    found = []

    def _cb(hwnd, _):
        if not _u32.IsWindowVisible(hwnd):
            return True
        n = _u32.GetWindowTextLengthW(hwnd)
        if n < 1:
            return True
        b = ctypes.create_unicode_buffer(n + 1)
        _u32.GetWindowTextW(hwnd, b, n + 1)
        t = b.value.lower()
        if namel in t or (len(base) > 3 and base in t):
            pid = wintypes.DWORD()
            _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            hp = _k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            if hp:
                img = ctypes.create_unicode_buffer(1024)
                sz  = wintypes.DWORD(1024)
                if _k32.QueryFullProcessImageNameW(hp, 0, img, ctypes.byref(sz)):
                    exe = os.path.basename(img.value).lower()
                    found.append(REPRODUCTORES_MAPA.get(exe, exe.replace(".exe","").upper()))
                _k32.CloseHandle(hp)
            return False
        return True

    try:
        _u32.EnumWindows(_EnumCB(_cb), 0)
    except Exception:
        pass
    return found[0] if found else "REPRODUCTOR"


# ---------------------------------------------------------------------------
#  THUMBNAIL EXTRACTION (Windows Shell IShellItemImageFactory, pure ctypes)
# ---------------------------------------------------------------------------
def _hbitmap_to_ppm_b64(hbm, tw, th):
    hdc    = _u32.GetDC(None)
    bmi    = struct.pack('<IiiHHIIiiII', 40, tw, -th, 1, 32, 0, 0, 0, 0, 0, 0) + b'\x00'*4
    bmi_b  = ctypes.create_string_buffer(bmi)
    px_buf = (ctypes.c_uint8 * (tw * th * 4))()
    ret    = _gdi.GetDIBits(hdc, hbm, 0, th, px_buf, bmi_b, 0)
    _u32.ReleaseDC(None, hdc)
    if not ret:
        return None
    header = f"P6\n{tw} {th}\n255\n".encode()
    raw    = bytes(px_buf)
    rgb    = bytearray(tw * th * 3)
    for i in range(tw * th):
        o = i * 4
        rgb[i*3]   = raw[o+2]
        rgb[i*3+1] = raw[o+1]
        rgb[i*3+2] = raw[o]
    return base64.b64encode(header + bytes(rgb)).decode('ascii')


def extract_thumb_bytes(filepath, tw=THUMB_W, th=THUMB_H):
    try:
        import os
        import cv2  # type: ignore
        import base64
        filepath = os.path.abspath(filepath)
        print(f"DEBUG EXTRACCIÓN: Procesando {filepath}")
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            log_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'AnimeTracker')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "tracker_debug.log"), "a", encoding="utf-8") as _log:
                _log.write(f"OpenCV Fallo: cap.isOpened() devolvio False para {filepath}\n")
            return None
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = int(total_frames * 0.25) if total_frames > 0 else 24
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            log_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'AnimeTracker')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "tracker_debug.log"), "a", encoding="utf-8") as _log:
                _log.write(f"OpenCV Fallo: cap.read() devolvio ret={ret} para {filepath} en el frame {target_frame}\n")
            return None
        # Redimensionar la miniatura (ancho de 200px para llenar tarjetas/mosaicos)
        height, width = frame.shape[:2]
        new_width = 200
        new_height = int(height * (new_width / width))
        resized = cv2.resize(frame, (new_width, new_height))
        
        # 1. Convertir BGR (OpenCV) a RGB
        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb_frame.shape
        
        # 2. Crear la cabecera PPM nativa que Tkinter lee sin errores
        header = f"P6\n{w} {h}\n255\n".encode('ascii')
        ppm_bytes = header + rgb_frame.tobytes()
        
        # 3. Retornar los bytes puros (Tkinter PhotoImage falla si se usa base64 para PPM)
        return ppm_bytes
    except Exception as e:
        log_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'AnimeTracker')
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "tracker_debug.log"), "a", encoding="utf-8") as _log:
            _log.write(f"OpenCV Fallo para {filepath}: {repr(e)}\n")
        return None


# ---------------------------------------------------------------------------
#  THUMBNAIL CACHE (async background loading)
# ---------------------------------------------------------------------------
class ThumbnailCache:
    _PENDING = object()

    def __init__(self, on_ready):
        self._on_ready = on_ready
        self._raw      = {}     # filepath -> b64 str | _PENDING | False(failed)
        self._photos   = {}     # filepath -> PhotoImage (main thread only)
        self._q        = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

    def get_b64(self, filepath):
        """Main-thread: return b64 if ready, else enqueue and return None."""
        raw = self._raw.get(filepath)
        if raw is None:
            self._raw[filepath] = self._PENDING
            self._q.put(filepath)
            return None
        if raw is self._PENDING or raw is False:
            return None
        return raw

    def get_photo(self, filepath):
        """Main-thread: return PhotoImage if ready, else None."""
        b64 = self.get_b64(filepath)
        if b64 is None:
            return None
        if filepath not in self._photos:
            try:
                self._photos[filepath] = tk.PhotoImage(data=b64)
            except Exception:
                self._raw[filepath] = False
                return None
        return self._photos[filepath]

    def _worker(self):
        import ctypes
        try:
            ctypes.windll.ole32.CoInitialize(None)
        except:
            pass
        while True:
            try:
                path = self._q.get(timeout=1)
                img_data  = extract_thumb_bytes(path)
                self._raw[path] = img_data if img_data else False
                try:
                    self._on_ready(path)
                except Exception:
                    pass
            except queue.Empty:
                pass
            except Exception:
                pass

    def clear(self):
        self._raw.clear()
        self._photos.clear()


# ---------------------------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------------------------
def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def truncar(text, n):
    return text if len(text) <= n else text[:n-1] + "..."

def badge_color(player):
    return {
        "CODEC MPC": C["badge_mpc"],
        "VLC":       C["badge_vlc"],
        "POTPLAYER": C["badge_pot"],
        "MPV":       C["badge_other"],
    }.get(player, C["badge_other"])


# ---------------------------------------------------------------------------
#  CUSTOM COLOR SYSTEM (simplified keys → internal C[] keys)
# ---------------------------------------------------------------------------
# Each simplified key maps to one or more internal C[] dict keys.
# Users configure only these 8 values; the app expands them automatically.
CUSTOM_COLOR_MAPPINGS = {
    "bg_root":      ("bg_root", "bg_header", "bg_footer"),
    "bg_card":      ("bg_card", "bg_list", "bg_row_normal"),
    "fg_texto":     ("fg_normal", "fg_title"),
    "fondo_ultimo": ("bg_row_last", "bg_card_last"),
    "texto_ultimo": ("fg_last",),
    "borde_activo": ("border_active",),
    "focus_border": ("focus_border",),
}

# Human-readable labels for the Settings window
CUSTOM_COLOR_LABELS = [
    ("bg_root",      "Fondo principal / cabecera"),
    ("bg_card",      "Fondo de lista / tarjetas"),
    ("fg_texto",     "Texto principal"),
    ("fondo_ultimo", "Fondo \u2714 Ultimo visto"),
    ("texto_ultimo", "Texto \u2714 Ultimo visto"),
    ("borde_activo", "Color de acento / borde"),
    ("focus_border", "Borde de enfoque (Teclado)"),
]


# ---------------------------------------------------------------------------
#  SETTINGS  —  with independent per-theme color profiles
# ---------------------------------------------------------------------------
class Settings:
    DEFAULTS = {
        "tema_actual":    "oscuro",
        "vista":          "lista",
        "fuente_familia": "Consolas",
        "fuente_tamano":  16,
        "colores_oscuro": {},   # custom colors for dark theme
        "colores_claro":  {},   # custom colors for light theme
        "carpetas_seguidas": [],
        "carpeta_activa": ""
    }

    @property
    def carpetas_seguidas(self): return self.data.get("carpetas_seguidas", [])
    @property
    def carpeta_activa(self): return self.data.get("carpeta_activa", "")
    
    def add_carpeta(self, ruta):
        if not getattr(self, '_is_valid_path', lambda x: True)(ruta): return
        if ruta not in self.data.get("carpetas_seguidas", []):
            self.data.setdefault("carpetas_seguidas", []).append(ruta)
        self.data["carpeta_activa"] = ruta
        self.save()
        
        import os, ctypes, json
        tr_path = os.path.join(ruta, ARCHIVO_REGISTRO)
        if not os.path.isfile(tr_path):
            try:
                with open(tr_path, "w", encoding="utf-8") as f:
                    json.dump({"ultimo_visto": ""}, f, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                ctypes.windll.kernel32.SetFileAttributesW(str(tr_path), 0x02)
            except Exception:
                pass
        
    def set_carpeta_activa(self, ruta):
        self.data["carpeta_activa"] = ruta
        self.save()
        
    def remove_carpeta(self, ruta):
        carpetas = self.data.get("carpetas_seguidas", [])
        if ruta in carpetas:
            carpetas.remove(ruta)
        self.data["carpetas_seguidas"] = carpetas
        if self.data.get("carpeta_activa", "") == ruta:
            self.data["carpeta_activa"] = carpetas[0] if carpetas else ""
        self.save()
        
        import os, ctypes
        tr_path = os.path.join(ruta, ARCHIVO_REGISTRO)
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(tr_path), 0x80)
            if os.path.isfile(tr_path):
                os.remove(tr_path)
        except Exception:
            pass

    def __init__(self, directory):
        import os
        config_dir = os.path.join(os.environ['APPDATA'], 'AnimeTracker')
        os.makedirs(config_dir, exist_ok=True)
        self._path = os.path.join(config_dir, ARCHIVO_SETTINGS)
        self.data  = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    # Migrate legacy key 'tema' → 'tema_actual'
                    if "tema" in d and "tema_actual" not in d:
                        d["tema_actual"] = d.pop("tema")
                    # Migrate legacy 'colores_personalizados' → current theme profile
                    if d.get("colores_personalizados"):
                        tema = d.get("tema_actual", "oscuro")
                        d.setdefault(f"colores_{tema}", {}).update(
                            d.pop("colores_personalizados"))
                    d.pop("colores_personalizados", None)
                    self.data.update(d)
            except Exception:
                pass
        # Ensure per-theme dicts always exist
        self.data.setdefault("colores_oscuro", {})
        self.data.setdefault("colores_claro", {})
        
        def is_valid(p):
            try:
                import sys, os
                if not p or not isinstance(p, str) or not os.path.isdir(p): return False
                
                p_abs = os.path.abspath(p).lower()
                cwd_abs = os.path.abspath(os.getcwd()).lower()
                exe_dir = os.path.abspath(os.path.dirname(sys.executable)).lower()
                script_dir = os.path.abspath(os.path.dirname(__file__)).lower()
                
                # Filter out exactly the root, dist, and executable folders
                if p_abs in (cwd_abs, exe_dir, script_dir):
                    return False
                    
                if os.path.basename(p_abs) == "dist":
                    return False
                    
                return True
            except: return False

        valid_carpetas = [c for c in self.data.get("carpetas_seguidas", []) if is_valid(c)]
        self.data["carpetas_seguidas"] = valid_carpetas
        if self.data.get("carpeta_activa") not in valid_carpetas:
            self.data["carpeta_activa"] = valid_carpetas[0] if valid_carpetas else ""
        self._is_valid_path = is_valid


    def save(self):
        try:
            import os
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando settings: {e}")

    def apply_theme(self):
        """Rebuild global C[] from base theme + per-theme custom overrides."""
        global C
        t    = self.data.get("tema_actual", "oscuro")
        base = TEMA_OSCURO if t == "oscuro" else TEMA_CLARO
        C.clear()
        C.update(base)
        # Expand simplified custom keys into all mapped C[] entries
        for simple_key, value in self.data.get(f"colores_{t}", {}).items():
            for c_key in CUSTOM_COLOR_MAPPINGS.get(simple_key, (simple_key,)):
                C[c_key] = value

    # ── Font helpers ─────────────────────────────────────────────────────────
    @property
    def fuente(self):
        """Bold content font for listbox and card titles."""
        return (self.data["fuente_familia"], self.data["fuente_tamano"], "bold")

    @property
    def fuente_ui(self):
        """Small non-bold font for UI chrome."""
        return ("Segoe UI", 9)

    # ── Theme ─────────────────────────────────────────────────────────────────
    @property
    def tema(self):      return self.data.get("tema_actual", "oscuro")
    @tema.setter
    def tema(self, v):   self.data["tema_actual"] = v

    # ── Vista ─────────────────────────────────────────────────────────────────
    @property
    def vista(self):     return self.data.get("vista", "lista")
    @vista.setter
    def vista(self, v):  self.data["vista"] = v

    # ── Font ──────────────────────────────────────────────────────────────────
    @property
    def fuente_familia(self): return self.data["fuente_familia"]
    @fuente_familia.setter
    def fuente_familia(self, v): self.data["fuente_familia"] = v

    @property
    def fuente_tamano(self): return self.data["fuente_tamano"]
    @fuente_tamano.setter
    def fuente_tamano(self, v): self.data["fuente_tamano"] = int(v)

    # ── Per-theme color helpers ───────────────────────────────────────────────
    def get_custom_colors(self, tema=None):
        """Return the mutable custom-color dict for the given (or current) theme."""
        t = tema or self.tema
        return self.data.setdefault(f"colores_{t}", {})

    def set_custom_color(self, simple_key, value, tema=None):
        """Store a simplified color override for the given (or current) theme."""
        t = tema or self.tema
        self.data.setdefault(f"colores_{t}", {})[simple_key] = value

    def reset_custom_colors(self, tema=None):
        """Clear all custom overrides for the given (or current) theme."""
        t = tema or self.tema
        self.data[f"colores_{t}"] = {}

    def get_effective_color(self, simple_key, tema=None):
        """
        Return the effective hex color for a simplified key.
        Checks custom overrides first, then falls back to the base theme.
        """
        t     = tema or self.tema
        custom = self.data.get(f"colores_{t}", {})
        if simple_key in custom:
            return custom[simple_key]
        base   = TEMA_OSCURO if t == "oscuro" else TEMA_CLARO
        c_keys = CUSTOM_COLOR_MAPPINGS.get(simple_key, (simple_key,))
        return base.get(c_keys[0], "#888888")


# ---------------------------------------------------------------------------
#  TOOLTIP
# ---------------------------------------------------------------------------
class Tooltip:
    def __init__(self, widget, text_fn):
        self._w = widget; self._fn = text_fn; self._tw = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, ev):
        t = self._fn(ev)
        if not t: return
        self._tw = tw = tk.Toplevel(self._w)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{ev.x_root+16}+{ev.y_root+10}")
        tw.configure(bg=C["border"], padx=1, pady=1)
        tk.Label(tw, text=t, bg=C["tooltip_bg"], fg=C["tooltip_fg"],
                 font=("Segoe UI", 8), padx=8, pady=4).pack()

    def _hide(self, _):
        if self._tw: self._tw.destroy(); self._tw = None


# ---------------------------------------------------------------------------
#  CARD VIEW
#
#  FIX v2.3:
#  - Thumbnail area is tk.Canvas (draws placeholder ▶ icon immediately)
#  - _relayout() uses grid() NOT place() → inner frame auto-sizes → scrollregion correct
#  - rebuild() calls update_idletasks() before reading canvas width
# ---------------------------------------------------------------------------
class CardView:
    CARD_W = 228
    CARD_H = 210
    GAP    = 10
    PAD    = 12

    def __init__(self, parent, app):
        self._app   = app
        self._cards = {}    # filename -> dict of card widgets
        self._order = []
        self._ncols = 3

        # ── Container (pack/forget to show/hide) ────────────────────────────
        self._container = tk.Frame(parent, bg=C["bg_list"])

        self._sb = tk.Scrollbar(self._container, orient="vertical",
                                bg=C["bg_scrollbar"], troughcolor=C["bg_list"],
                                width=8, relief="flat", bd=0)
        self._canvas = tk.Canvas(self._container, bg=C["bg_list"],
                                 highlightthickness=0, bd=0)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.configure(command=self._canvas.yview)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Inner frame lives inside the canvas
        self._inner = tk.Frame(self._canvas, bg=C["bg_list"])
        self._win_id = self._canvas.create_window(
            (self.PAD, self.PAD), window=self._inner, anchor="nw")

        # When inner frame content changes size, update scroll region
        self._inner.bind("<Configure>", self._on_inner_configure)

        # When canvas is resized, update inner frame width and relayout
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Mousewheel scroll
        for w in [self._canvas, self._inner]:
            w.bind("<MouseWheel>", self._scroll)
            w.bind("<Button-1>", lambda e, wid=w: self._app._force_focus(-1) if e.widget == wid else None)

    # ── Scroll region ────────────────────────────────────────────────────────
    def _on_inner_configure(self, ev):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    # ── Canvas resize: update inner width + relayout if cols changed ─────────
    def clear(self):
        for w in self._inner.winfo_children():
            w.destroy()
        self._cards.clear()
        self._order.clear()

    def _on_canvas_resize(self, ev):
        # Keep inner frame width = canvas width (minus scrollbar padding)
        self._canvas.itemconfig(self._win_id, width=ev.width - self.PAD * 2)
        nc = max(1, (ev.width - self.PAD * 2) // (self.CARD_W + self.GAP))
        if nc != self._ncols:
            self._ncols = nc
            self._relayout()

    # ── Public API ───────────────────────────────────────────────────────────
    def pack_forget(self):
        self._container.pack_forget()

    def pack(self):
        self._container.pack(fill="both", expand=True)

    def rebuild(self, videos, directory, ultimo, cache):
        # 1. Clear old cards
        for w in self._inner.winfo_children():
            w.destroy()
        self._cards.clear()
        self._order = list(videos)

        dark = self._app.settings.tema == "oscuro"

        # 2. Build ALL cards IMMEDIATELY with placeholder thumbnail canvas
        for filename in videos:
            filepath = os.path.join(directory, filename)
            self._cards[filename] = self._make_card(filename, filepath, cache, dark)

        # 3. Force geometry resolution so winfo_width() is reliable
        #    FIX: this is the critical call that prevents blank screen
        self._container.update_idletasks()
        cw = self._canvas.winfo_width()
        if cw <= 1:
            # Canvas not yet rendered; estimate from root window
            cw = self._container.winfo_width()
        if cw <= 1:
            cw = 860  # safe fallback

        self._ncols = max(1, (cw - self.PAD * 2) // (self.CARD_W + self.GAP))

        # 4. Layout with grid()
        self._relayout()

        # 5. Apply state colors/badges
        self.update_states(ultimo)

        # 6. Kick off async thumbnail loading for visible cards
        for filename in videos:
            filepath = os.path.join(directory, filename)
            photo = cache.get_photo(filepath)
            if photo:
                self.update_thumbnail(filepath, cache)
            else:
                cache.get_b64(filepath)  # enqueues if not already pending

    # ── Card state colors ─────────────────────────────────────────────────────
    def update_states(self, ultimo):
        for fn, w in self._cards.items():
            frm   = w["frame"]
            badge = w["badge"]
            title = w["title"]
            num   = w["num"]
            tcv   = w["thumb_cv"]

            if fn == ultimo:
                bg_c     = C["bg_card_last"]; fg_c = C["fg_last"]
                border_c = C["fg_last"];      bthick = 2
                badge.configure(text="\u2714 ULTIMO VISTO", fg=C["fg_last"])
                frm.configure(bg=bg_c,
                              highlightbackground=border_c,
                              highlightthickness=bthick)
                title.configure(bg=bg_c, fg=fg_c)
                badge.configure(bg=bg_c)
                num.configure(bg=bg_c, fg=fg_c)
                tcv.configure(bg=bg_c)
            else:
                frm.configure(bg=C["bg_card"],
                              highlightbackground=C["border_card"],
                              highlightthickness=1)
                title.configure(bg=C["bg_card"], fg=C["fg_title"])
                badge.configure(bg=C["bg_card"], fg=C["fg_sub"], text="")
                num.configure(bg=C["bg_card"], fg=C["fg_sub"])
                tcv.configure(bg=C["thumb_bg"])

    def set_focus(self, idx):
        self.update_states(self._app.ultimo_visto)
        if idx < 0 or idx >= len(self._order): return
        fn = self._order[idx]
        d = self._cards.get(fn)
        if d:
            d["frame"].config(highlightbackground=C.get("focus_border", "#ffff00"), highlightthickness=3)
            y = d["frame"].winfo_y()
            h = d["frame"].winfo_height()
            ch = self._canvas.winfo_height()
            top = self._canvas.canvasy(0)
            bottom = top + ch
            if y < top or y + h > bottom:
                scroll_y = max(0, y - 10)
                self._canvas.yview_moveto(scroll_y / max(1, self._inner.winfo_height()))

    # ── Update thumbnail when background thread finishes ─────────────────────
    def update_thumbnail(self, filepath, cache):
        fn = os.path.basename(filepath)
        if fn not in self._cards:
            return
        photo = cache.get_photo(filepath)
        if photo is None:
            return   # still loading or failed — placeholder stays
        tcv = self._cards[fn]["thumb_cv"]
        tcv.delete("all")
        # Draw the real thumbnail image centered
        tcv.create_image(100, 56, anchor="center", image=photo)
        # Keep reference to prevent GC
        self._cards[fn]["photo_ref"] = photo
        tcv.image = photo  # <-- Vital para evitar el garbage collection de Tkinter!

    # ── Theme re-apply (container widgets) ───────────────────────────────────
    def apply_theme(self):
        self._container.configure(bg=C["bg_list"])
        self._canvas.configure(bg=C["bg_list"])
        self._inner.configure(bg=C["bg_list"])
        self._sb.configure(bg=C["bg_scrollbar"], troughcolor=C["bg_list"])

    # ── Internal ─────────────────────────────────────────────────────────────
    def _make_card(self, filename, filepath, cache, dark):
        """Build a card Frame with placeholder thumbnail canvas — renders immediately."""
        frm = tk.Frame(
            self._inner,
            bg=C["bg_card"],
            highlightthickness=1,
            highlightbackground=C["border_card"],
            cursor="hand2",
            width=self.CARD_W,
            height=self.CARD_H,
        )
        frm.pack_propagate(False)   # keep fixed width/height
        frm._is_video_item = True

        # ── Thumbnail canvas (renders immediately with placeholder) ──────────
        tcv = tk.Canvas(
            frm,
            width=THUMB_W, height=THUMB_H,
            bg=C["thumb_bg"],
            highlightthickness=0, bd=0,
        )
        tcv.pack(fill="x", padx=4, pady=(4, 2))
        # Draw placeholder: filled rect + circular play button + "▶" text
        cx, cy = THUMB_W // 2, THUMB_H // 2
        r = 22
        tcv.create_rectangle(0, 0, THUMB_W, THUMB_H,
                             fill=C["thumb_bg"], outline="")
        tcv.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=C["thumb_icon"], outline=C["border"])
        tcv.create_text(cx+2, cy, text="\u25b6", font=("Segoe UI", 14, "bold"),
                       fill=C["thumb_play"], anchor="center")

        # ── Episode number ───────────────────────────────────────────────────
        idx = self._order.index(filename) + 1 if filename in self._order else 0
        num = tk.Label(frm, text=f"#{idx:02d}",
                       font=("Segoe UI", 7),
                       bg=C["bg_card"], fg=C["fg_sub"], anchor="e")
        num.pack(fill="x", padx=6)

        # ── Title (uses configured font+size+bold) ───────────────────────────
        title = tk.Label(
            frm, text=truncar(os.path.splitext(filename)[0], 28),
            font=self._app.settings.fuente,   # FIX: uses full bold font from settings
            bg=C["bg_card"], fg=C["fg_title"],
            wraplength=self.CARD_W - 14, anchor="w", justify="left",
        )
        title.pack(fill="x", padx=6, pady=(1, 0))

        # ── Status badge ─────────────────────────────────────────────────────
        badge = tk.Label(frm, text="", font=("Segoe UI", 8),
                         bg=C["bg_card"], fg=C["fg_sub"])
        badge.pack(fill="x", padx=6, pady=(0, 3))

        # ── Bind interactions to all sub-widgets ─────────────────────────────
        for widget in [frm, tcv, title, badge, num]:
            widget.bind("<Button-1>",
                lambda e, fn=filename: self._app._force_focus(self._app.videos.index(fn) if fn in getattr(self._app, 'videos', []) else 0))
            widget.bind("<Double-Button-1>",
                lambda e, fn=filename: self._app._play_file(fn))
            widget.bind("<MouseWheel>", self._scroll)

        return {
            "frame": frm, "thumb_cv": tcv,
            "title": title, "badge": badge, "num": num,
        }

    # ── FIX: use grid() — frame auto-sizes, scrollregion computed correctly ──
    def _relayout(self):
        ncols = max(1, self._ncols)

        # Remove all cards from grid first
        for fn in self._order:
            if fn in self._cards:
                self._cards[fn]["frame"].grid_remove()

        # Re-grid all cards
        for i, fn in enumerate(self._order):
            if fn not in self._cards:
                continue
            r, c = divmod(i, ncols)
            self._cards[fn]["frame"].grid(
                row=r, column=c,
                padx=(0, self.GAP),
                pady=(0, self.GAP),
                sticky="nw",
            )

        # Ensure uniform column widths
        for c in range(ncols):
            self._inner.columnconfigure(c, weight=0, minsize=self.CARD_W)

        # Force canvas to recalculate scrollregion
        self._inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _hover_card(self, frm, filename, entering):
        if filename == self._app.ultimo_visto:
            return
        bg = C["bg_card_hover"] if entering else C["bg_card"]
        brd = C["border_active"] if entering else C["border_card"]
        frm.configure(bg=bg, highlightbackground=brd, highlightthickness=1)
        for w in frm.winfo_children():
            try:
                w.configure(bg=bg)
            except Exception:
                pass

    def _scroll(self, ev):
        self._canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")


# ---------------------------------------------------------------------------
#  SETTINGS WINDOW
# ---------------------------------------------------------------------------
class VentanaConfiguracion(tk.Toplevel):

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._st = app.settings
        self._apply = app._apply_theme_all
        self._pending  = {"oscuro": {}, "claro": {}}  # per-theme pending color overrides
        self._swatches = {}                            # simple_key -> swatch Label widget

        self._tema_v   = tk.StringVar(value=self._st.tema)
        self._fuente_v = tk.StringVar(value=self._st.fuente_familia)
        self._tamano_v = tk.IntVar(value=self._st.fuente_tamano)

        self.title("Configuracion")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=C["bg_header"])

        try:
            import sys
            import os
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "gear.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                logo_path = os.path.join(base_path, "logo.ico")
                if os.path.exists(logo_path):
                    self.iconbitmap(logo_path)
        except Exception:
            pass

        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h   = 530, 520
        self.geometry(f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}")

        self._build()

    def _build(self):
        bg = C["bg_header"]
        tk.Frame(self, bg=C["border_active"], height=3).pack(fill="x")
        tk.Label(self, text="  Configuracion de Apariencia",
                 font=("Segoe UI", 12, "bold"),
                 bg=bg, fg=C["fg_title"], pady=10).pack(fill="x")
        tk.Frame(self, bg=C["separator"], height=1).pack(fill="x")

        # Action buttons (packed first to reserve bottom space)
        tk.Frame(self, bg=C["separator"], height=1).pack(fill="x", side="bottom")
        bar = tk.Frame(self, bg=bg, pady=10); bar.pack(fill="x", side="bottom")
        self._btn(bar, "Guardar y Aplicar", self._save,
                  C["border_active"], "#000").pack(side="right", padx=(0, 14))
        self._btn(bar, "Cancelar",          self.destroy,
                  C["bg_btn"], C["fg_btn"]).pack(side="right", padx=6)

        # Static body
        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True)

        p = {"padx": 20, "pady": 4}

        # Section 1: Theme
        self._sec(body, "1.  Modo de color", is_first=True)
        rf = tk.Frame(body, bg=bg); rf.pack(fill="x", **p)
        for val, lbl in [("oscuro", "Modo Oscuro (Catppuccin)"),
                          ("claro",  "Modo Claro")]:
            tk.Radiobutton(rf, text=lbl, variable=self._tema_v, value=val,
                bg=bg, fg=C["fg_normal"], selectcolor=C["bg_btn"],
                activebackground=bg, activeforeground=C["fg_title"],
                font=("Segoe UI", 10),
                command=self._preview_tema).pack(anchor="w", pady=2)

        # Section 2: Per-theme custom colors
        self._sec(body, "2.  Colores \u2014 perfil independiente por tema")
        tk.Label(body, text="  Cada tema conserva sus colores de forma independiente",
                 font=("Segoe UI", 8), bg=bg,
                 fg=C["fg_sub"]).pack(anchor="w", padx=20)
        for key, label in CUSTOM_COLOR_LABELS:
            self._color_row(body, key, label, bg)

        # Section 3: Font
        self._sec(body, "3.  Tipografia")
        ff = tk.Frame(body, bg=bg); ff.pack(fill="x", padx=20, pady=6)
        tk.Label(ff, text="Fuente:", font=("Segoe UI", 9),
                 bg=bg, fg=C["fg_normal"], width=12, anchor="w").grid(row=0, column=0)
        # Previsualizacion de fuentes (OptionMenu en lugar de ttk.Combobox para soportar fuente individual por opcion)
        opt = tk.OptionMenu(ff, self._fuente_v, *FUENTES)
        self.fuente_menu = opt
        opt.config(width=20, bg=C["bg_btn"], fg=C["fg_normal"], activebackground=C["bg_btn_hover"], 
                   activeforeground=C["fg_normal"], relief="flat", highlightthickness=1, 
                   highlightbackground=C["border"], highlightcolor=C["border_active"], font=("Segoe UI", 9))
        
        # Modificar el menu desplegable para que cada fuente use su propia tipografia
        menu = opt["menu"]
        menu.config(bg=C["bg_btn"], fg=C["fg_normal"], activebackground=C["bg_btn_hover"])
        for i, font_name in enumerate(FUENTES):
            menu.entryconfig(i, font=(font_name, 11))
            
        opt.grid(row=0, column=1, sticky="w")
        tk.Label(ff, text="Tamano:", font=("Segoe UI", 9),
                 bg=bg, fg=C["fg_normal"], width=12, anchor="w").grid(row=1, column=0, pady=6)
        tk.Spinbox(ff, textvariable=self._tamano_v, from_=10, to=28,
                   width=5, bg=C["bg_btn"], fg=C["fg_normal"],
                   buttonbackground=C["bg_btn"], relief="flat",
                   font=("Segoe UI", 9)).grid(row=1, column=1, sticky="w")
        tk.Label(ff, text="pt  (16 recomendado, estilo bold)",
                 font=("Segoe UI", 8), bg=bg, fg=C["fg_sub"]
                 ).grid(row=1, column=2, padx=6)
        tk.Frame(body, bg=bg, height=20).pack()
        
        # Reset button inside scrollable area
        reset_bar = tk.Frame(body, bg=bg)
        reset_bar.pack(fill="x", pady=(0, 20))
        self._btn(reset_bar, "Restaurar colores por defecto", self._reset,
                  "#DC143C", "#FFFFFF").pack()



    def _sec(self, p, t, is_first=False):
        bg = C["bg_header"]
        if not is_first:
            tk.Frame(p, bg=C["separator"], height=1).pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(p, text=t, font=("Segoe UI", 10, "bold"),
                 bg=bg, fg=C["fg_title"]).pack(anchor="w", padx=20, pady=(4 if not is_first else 0, 2))

    def _color_row(self, parent, key, label, bg):
        """Color picker row for a simplified color key (per-theme aware)."""
        f = tk.Frame(parent, bg=bg); f.pack(fill="x", padx=20, pady=3)
        tk.Label(f, text=label, font=("Segoe UI", 9),
                 bg=bg, fg=C["fg_normal"], width=30, anchor="w").pack(side="left")

        # Show the currently effective color (pending > custom > base theme)
        tema = self._tema_v.get()
        col  = self._pending[tema].get(key, self._st.get_effective_color(key, tema))
        sw   = tk.Label(f, text="      ", bg=col,
                        relief="groove", bd=1, cursor="hand2")
        sw.pack(side="left", padx=(0, 6))
        self._swatches[key] = sw   # track for reload on theme switch

        def pick(k=key, s=sw):
            t   = self._tema_v.get()
            ini = self._pending[t].get(k, self._st.get_effective_color(k, t))
            res = colorchooser.askcolor(color=ini, title=f"Color: {k}", parent=self)
            if res and res[1]:
                self._pending[t][k] = res[1]
                s.configure(bg=res[1])

        sw.bind("<Button-1>", lambda e, k=key: pick(k))
        b = tk.Label(f, text="Elegir", font=("Segoe UI", 8), cursor="hand2",
                     bg=C["bg_btn"], fg=C["fg_btn"], padx=6, pady=2)
        b.bind("<Button-1>", lambda e, k=key: pick(k))
        b.bind("<Enter>", lambda e: b.configure(bg=C["bg_btn_hover"]))
        b.bind("<Leave>", lambda e: b.configure(bg=C["bg_btn"]))
        b.pack(side="left")

    def _reload_swatches(self, tema):
        """Reload all color swatches to reflect the given theme\'s profile."""
        for sk, sw in self._swatches.items():
            col = self._pending[tema].get(
                sk, self._st.get_effective_color(sk, tema))
            try:
                sw.configure(bg=col)
            except Exception:
                pass

    def _btn(self, parent, text, cmd, bg, fg):
        b = tk.Label(parent, text=f"  {text}  ",
                     font=("Segoe UI", 9, "bold"), cursor="hand2",
                     bg=bg, fg=fg, padx=4, pady=6)
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def _preview_tema(self):
        """Switch the live preview to the selected theme."""
        nuevo = self._tema_v.get()
        self._st.tema = nuevo
        self._st.apply_theme()
        # Reload swatches for the newly selected theme (preserves its profile)
        self._reload_swatches(nuevo)
        self._apply()
        # Also refresh this config window's own colors instantly
        self._refresh_self_theme()

    def _refresh_self_theme(self):
        """Repaint the config window itself to match the new theme (fix #2)."""
        bg = C["bg_header"]
        fg_title  = C["fg_title"]
        fg_normal = C["fg_normal"]
        try:
            self.configure(bg=bg)
            def _walk(w):
                try:
                    cls = type(w).__name__
                    if cls == "Frame":
                        w.configure(bg=bg)
                    elif cls == "Label":
                        # Accent separator frames are tk.Frame, not Label — safe to repaint
                        cur_bg = w.cget("bg")
                        # Keep the red accent bar and red buttons as-is
                        if cur_bg not in (C["border_active"], "#DC143C"):
                            w.configure(bg=bg, fg=fg_title)
                    elif cls == "Radiobutton":
                        w.configure(bg=bg, fg=fg_normal, selectcolor=C["bg_btn"],
                                    activebackground=bg, activeforeground=fg_title)
                    elif cls == "Button":
                        cur_bg = w.cget("bg")
                        if cur_bg not in (C["border_active"], "#DC143C"):
                            w.configure(bg=C["bg_btn"], fg=fg_normal,
                                        activebackground=C["bg_btn_hover"])
                    elif cls == "Spinbox":
                        w.configure(bg=C["bg_btn"], fg=fg_normal, buttonbackground=C["bg_btn"])
                except Exception:
                    pass
                for child in w.winfo_children():
                    _walk(child)
            _walk(self)
            
            if hasattr(self, "fuente_menu"):
                self.fuente_menu.config(bg=C["bg_btn"], fg=fg_normal, activebackground=C["bg_btn_hover"], activeforeground=fg_normal)
                self.fuente_menu["menu"].config(bg=C["bg_btn"], fg=fg_normal, activebackground=C["bg_btn_hover"])
        except Exception:
            pass

    def _save(self):
        self._st.tema = self._tema_v.get()
        self._st.fuente_familia = self._fuente_v.get()
        self._st.fuente_tamano = self._tamano_v.get()
        for t in ["oscuro", "claro"]:
            for k, v in self._pending[t].items():
                self._st.data[f"colores_{t}"][k] = v
        self._st.apply_theme()
        self._st.save()
        if self._apply:
            self._apply()
        self.destroy()

    def _reset(self):
        """Reset custom colors for the CURRENT selected theme and font defaults."""
        tema = self._tema_v.get()
        self._st.tema = tema
        self._st.reset_custom_colors(tema)
        self._pending[tema].clear()
        
        # Restaurar fuentes por defecto
        def_font = self._st.DEFAULTS["fuente_familia"]
        def_size = self._st.DEFAULTS["fuente_tamano"]
        self._fuente_v.set(def_font)
        self._tamano_v.set(def_size)
        self._st.fuente_familia = def_font
        self._st.fuente_tamano = def_size

        self._st.apply_theme()
        self._reload_swatches(tema)
        self._st.save()  # Solo guarda settings, NO toca .tracker.json
        self._apply()
        # No destruimos la ventana para que el usuario vea el cambio al instante



        self.destroy()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
#  MOSAICOS VIEW (Tiles)
# ---------------------------------------------------------------------------
class MosaicosView:
    def __init__(self, parent, app):
        self._app   = app
        self._tiles = {}
        self._order = []
        self._ncols = 2

        self._container = tk.Frame(parent, bg=C["bg_list"])
        self._sb = tk.Scrollbar(self._container, orient="vertical",
                                bg=C["bg_scrollbar"], troughcolor=C["bg_list"],
                                width=8, relief="flat", bd=0)
        self._canvas = tk.Canvas(self._container, bg=C["bg_list"],
                                 highlightthickness=0, bd=0)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._canvas.config(yscrollcommand=self._sb.set)
        self._sb.config(command=self._canvas.yview)

        self._inner = tk.Frame(self._canvas, bg=C["bg_list"])
        self._win_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.config(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        for w in (self._canvas, self._inner):
            w.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            w.bind("<Button-1>", lambda e, wid=w: self._app._force_focus(-1) if e.widget == wid else None)

    def clear(self):
        for w in self._inner.winfo_children():
            w.destroy()
        self._tiles.clear()
        self._order.clear()

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._win_id, width=event.width)
        w = event.width
        if w < 100: w = 800
        # responsive logic: 1 col < 500, 2 cols < 800, 3 cols >= 800
        cols = max(1, w // 380)
        if cols != self._ncols:
            self._ncols = cols
            self._relayout()

    def _relayout(self):
        for i in range(self._ncols):
            self._inner.columnconfigure(i, weight=1)
        for idx, fn in enumerate(self._order):
            if fn in self._tiles:
                r = idx // self._ncols
                c = idx % self._ncols
                self._tiles[fn]["frame"].grid(row=r, column=c, padx=6, pady=6, sticky="ew")
        self._app.root.update_idletasks()

    def pack(self):
        self._container.pack(fill="both", expand=True)

    def pack_forget(self):
        self._container.pack_forget()

    def update_thumbnail(self, filepath, cache):
        fn = os.path.basename(filepath)
        if fn not in self._tiles: return
        tcv = self._tiles[fn]["thumb_cv"]
        photo = cache.get_photo(filepath)
        if photo:
            # Subsample 200x112 -> 100x56 to fit mosaic thumbnail area
            small = photo.subsample(2, 2)
            self._tiles[fn]["small_photo"] = small  # keep reference
            tcv.delete("all")
            tcv.create_image(50, 28, image=small, anchor="center")
            tcv.image = small  # <-- Vital para evitar el garbage collection de Tkinter!

    def rebuild(self, videos, dirpath, ult, cache):
        self._order = list(videos)
        for w in self._inner.winfo_children():
            w.destroy()
        self._tiles.clear()

        # Build each tile
        for idx, fn in enumerate(self._order):
            tf = tk.Frame(self._inner, bg=C["bg_card"], bd=3, relief="flat", cursor="hand2")
            
            # Left: Thumbnail canvas 100x56
            tcv = tk.Canvas(tf, width=100, height=56, bg=C["thumb_bg"], highlightthickness=0, bd=0)
            tcv.pack(side="left", padx=4, pady=4)
            # draw placeholder
            tcv.create_polygon(40, 18, 40, 38, 60, 28, fill=C["thumb_play"])
            
            # Right: text container
            rf = tk.Frame(tf, bg=C["bg_card"])
            rf.pack(side="left", fill="both", expand=True, padx=8, pady=4)
            
            title = tk.Label(rf, text=f" {idx+1:>3}   {truncar(fn, 50)}",
                             font=self._app.settings.fuente, bg=C["bg_card"], fg=C["fg_normal"], anchor="w")
            title.pack(side="top", fill="x", anchor="w")
            
            status = tk.Label(rf, text="", font=("Segoe UI", 8, "bold"),
                              bg=C["bg_card"], fg=C["fg_sub"], anchor="w")
            status.pack(side="top", fill="x", anchor="w", pady=(2,0))

            d = {"frame": tf, "thumb_cv": tcv, "title": title, "status": status, "rf": rf}
            self._tiles[fn] = d

            # Binds
            for w in (tf, tcv, rf, title, status):
                w.bind("<Button-1>", lambda e, f=fn: self._app._force_focus(self._order.index(f) if f in self._order else 0))
                w.bind("<Double-Button-1>", lambda e, f=fn: self._app._play_file(f))
                w.bind("<Enter>", lambda e, f=fn: self._on_hover(f))
                w.bind("<Leave>", lambda e, f=fn: self._on_leave(f))

            filepath = os.path.join(dirpath, fn)
            photo = cache.get_photo(filepath)
            if photo:
                self.update_thumbnail(filepath, cache)
            else:
                cache.get_b64(filepath)

        self.update_states(ult)
        self._app.root.update_idletasks()
        w = self._canvas.winfo_width()
        if w < 100: w = 800
        self._ncols = max(1, w // 380)
        self._relayout()


    def set_focus(self, idx):
        self.update_states(self._app.ultimo_visto)
        if idx < 0 or idx >= len(self._order): return
        fn = self._order[idx]
        d = self._tiles.get(fn)
        if d:
            d["frame"].config(highlightbackground=C.get("focus_border", "#ffff00"), highlightthickness=3)
            y = d["frame"].winfo_y()
            h = d["frame"].winfo_height()
            ch = self._canvas.winfo_height()
            top = self._canvas.canvasy(0)
            bottom = top + ch
            if y < top or y + h > bottom:
                scroll_y = max(0, y - 10)
                self._canvas.yview_moveto(scroll_y / max(1, self._inner.winfo_height()))

    def update_states(self, ult):
        for fn, d in self._tiles.items():
            tf, title, status, rf = d["frame"], d["title"], d["status"], d["rf"]
            if fn == ult:
                tf.config(bg=C["border"], highlightbackground=C["fg_last"], highlightthickness=2)
                rf.config(bg=C["bg_card_last"])
                title.config(bg=C["bg_card_last"], fg=C["fg_last"])
                status.config(bg=C["bg_card_last"], fg=C["fg_last"], text="[✔ ULTIMO VISTO]")
            else:
                tf.config(bg=C["border_card"], highlightbackground=C["border_card"], highlightthickness=1)
                rf.config(bg=C["bg_card"])
                title.config(bg=C["bg_card"], fg=C["fg_normal"])
                status.config(bg=C["bg_card"], text="")

    def _on_hover(self, fn):
        if fn not in self._tiles or fn == self._app.ultimo_visto: return
        d = self._tiles[fn]
        d["rf"].config(bg=C["bg_card_hover"]); d["title"].config(bg=C["bg_card_hover"])
        d["status"].config(bg=C["bg_card_hover"])

    def _on_leave(self, fn):
        if fn not in self._tiles or fn == self._app.ultimo_visto: return
        d = self._tiles[fn]
        d["rf"].config(bg=C["bg_card"]); d["title"].config(bg=C["bg_card"])
        d["status"].config(bg=C["bg_card"])

    def apply_theme(self):
        self._container.config(bg=C["bg_list"])
        self._canvas.config(bg=C["bg_list"])
        self._sb.config(bg=C["bg_scrollbar"], troughcolor=C["bg_list"])
        self._inner.config(bg=C["bg_list"])
        self.update_states(self._app.ultimo_visto)


#  MAIN APPLICATION
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
#  WINDOW WATCHER — Auto-Sync por título de ventana activa
# ---------------------------------------------------------------------------

# Patrones regex ordenados de mayor a menor especificidad
_EP_PATTERNS = [
    re.compile(r'[Ss]\d{1,2}[Ee](\d{1,3})'),           # S02E05
    re.compile(r'[Ee]p(?:isode|isodio)?\.?\s*(\d{1,3})'), # Ep 12 / Episode 12
    re.compile(r'[Cc]ap(?:\u00edtulo|itulo)?\.?\s*(\d{1,3})'), # Cap 7 / Cap\u00edtulo 07
    re.compile(r'[-\u2013\u2014]\s*(\d{1,3})\s*[-\u2013\u2014\[]'),  # - 08 - / - 24 [
    re.compile(r'[Ee](\d{2,3})\b'),                      # E042
    re.compile(r'\b(\d{2,3})\b'),                        # \u00faltimo recurso: 2-3 d\u00edgitos
]


class WindowWatcher:
    """Hilo daemon que monitorea el título de la ventana en primer plano
    y detecta qué video se está reproduciendo.
    
    Thread-safe: se comunica con Tkinter únicamente via queue.Queue.
    Sin dependencias externas: usa ctypes puro (windll.user32).
    """

    def __init__(self):
        self._thread   = None
        self._stop_evt = threading.Event()
        self._videos   = []
        self._dirpath  = ""
        self._queue    = None

    # ------------------------------------------------------------------ public
    def start(self, videos: list, dirpath: str, out_queue: queue.Queue):
        """Arranca (o reinicia) el hilo watcher con una lista nueva de videos."""
        self._videos  = list(videos)
        self._dirpath = dirpath
        self._queue   = out_queue
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="WindowWatcher")
        self._thread.start()
        
    def update_context(self, videos: list, dirpath: str):
        self._videos = list(videos)
        self._dirpath = dirpath
        if self._thread and self._thread.is_alive():
            return  # ya corriendo; la lista se actualizó in-place
        self._stop_evt.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="WindowWatcher"
        )
        self._thread.start()

    def update_videos(self, videos: list, dirpath: str):
        """Actualiza la lista de videos sin reiniciar el hilo."""
        self._videos  = list(videos)
        self._dirpath = dirpath

    def stop(self):
        """Para el hilo de forma limpia."""
        self._stop_evt.set()

    # ----------------------------------------------------------------- private
    def _run(self):
        import os, json, ctypes
        while not self._stop_evt.is_set():
            if not self._videos or not self._dirpath:
                self._stop_evt.wait(SYNC_INTERVAL_S)
                continue
            try:
                title = self._get_player_title()
                if title:
                    match = self._match_video(title)
                    if match:
                        if match != getattr(self, '_last_match', None):
                            self._last_match = match
                            if self._queue is not None:
                                self._queue.put(match)
                    else:
                        self._last_match = None
                else:
                    self._last_match = None
            except Exception:
                pass  # jamás dejar caer el hilo
            self._stop_evt.wait(SYNC_INTERVAL_S)

    def _get_player_title(self) -> str:
        """Escanea todas las ventanas visibles buscando un título que coincida con _match_video."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            
            found_title = ""
            
            def enum_windows_proc(hwnd, lParam):
                nonlocal found_title
                try:
                    if not user32.IsWindowVisible(hwnd):
                        return True
                    
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        if buf.value:
                            title = buf.value
                            # If it matches our universal video regex/filename, we found it!
                            if self._match_video(title):
                                found_title = title
                                return False # Stop searching
                except Exception:
                    pass
                return True

            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
            return found_title
        except Exception:
            return ""

    def _match_video(self, win_title: str) -> str:
        # Ignore our own window so 'v2.3' doesn't get parsed as chapter 3
        if "Anime & Video Tracker" in win_title or "AnimeTracker" in win_title:
            return None
            
        import re
        title_lower = win_title.lower()

        for v in self._videos:
            name_no_ext = os.path.splitext(v)[0].lower()
            if len(name_no_ext) > 4 and name_no_ext in title_lower:
                return v

        ep_num = None
        patrones = list(_EP_PATTERNS)
        patrones.append(re.compile(r'\b0*(\d{1,4})\b(?:\.\w{3,4})?$'))
        for pat in patrones:
            m = pat.search(win_title)
            if m:
                ep_num = int(m.group(1))
                break
        if ep_num is None:
            return None

        # Buscar video cuyo nombre contenga ese n\u00famero
        ep_str_2 = f"{ep_num:02d}"
        ep_str_3 = f"{ep_num:03d}"
        for v in self._videos:
            vl = v.lower()
            if ep_str_3 in vl or ep_str_2 in vl:
                return v
        return None


class VideoTrackerApp:
    POLL_MS = 1000

    def __init__(self, root):
        self.root = root

        if getattr(sys, "frozen", False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))

        self.settings = Settings(self.app_dir)
        self.settings.apply_theme()
        
        self.directorio = self.settings.carpeta_activa
        self._cfg_window()

        # State
        self.videos             = []
        self.ultimo_visto       = ""
        self._hover_idx         = -1
        self._focus_index       = -1

        # Async thumbnail cache
        self._thumb_cache = ThumbnailCache(self._on_thumb_ready)

        # UI refs
        self._btns         = []
        self._cb_vista     = None
        self._vista_var    = tk.StringVar()
        self._card_view    = None
        self._mos_view     = None
        self._list_cont    = None
        self._vista_actual = self.settings.vista

        self.ultimo_visto = self._load_progress()
        self._build_ui()
        self._refresh_videos()
        if self._vista_actual in ("tarjetas", "mosaicos"):
            self._rebuild_cards()
        self._update_ui()

        # ── Auto-sync por título de ventana ──────────────────────────────────
        self._sync_queue = queue.Queue()
        self._watcher    = WindowWatcher()
        self._watcher.start(self.videos, self.directorio, self._sync_queue)
        self._poll_sync_queue()

        # Parar el watcher al cerrar la ventana
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._empty_state_frame = None
        
        if not self.directorio:
            self._show_empty_state()

    def cambiar_carpeta_activa(self, nueva_ruta):
        import os
        import tkinter as tk
        if hasattr(self, '_flush_sync_queue'):
            self._flush_sync_queue()
            
        if not nueva_ruta or not os.path.isdir(nueva_ruta):
            self.directorio = ""
            self.settings.set_carpeta_activa("")
            self.videos = []
            self.ultimo_visto = ""
            if hasattr(self, '_card_view') and self._card_view: self._card_view.clear()
            if hasattr(self, '_mos_view') and self._mos_view: self._mos_view.clear()
            if hasattr(self, 'listbox') and self.listbox: self.listbox.delete(0, tk.END)
            self._update_labels()
            self._show_empty_state()
            return
            
        self.settings.set_carpeta_activa(nueva_ruta)
        self.directorio = nueva_ruta
        self.ultimo_visto = self._load_progress()
        self._refresh_videos()
        if self._empty_state_frame:
            self._empty_state_frame.pack_forget()
        if hasattr(self, '_outer') and self._outer:
            self._outer.pack(fill="both", expand=True)
        
        # Reset views
        if self._card_view: self._card_view.clear()
        if self._mos_view: self._mos_view.clear()
        
        if self._vista_actual in ("tarjetas", "mosaicos"):
            self._rebuild_cards()
        self._update_ui()
        self.root.update_idletasks()
        if hasattr(self, '_watcher'):
            self._watcher.update_videos(self.videos, self.directorio)
        
    def _show_empty_state(self):
        import tkinter as tk
        # Hide if folder manager is currently visible (fix #4)
        if getattr(self, '_fm_frame', None) and self._fm_frame and self._fm_frame.winfo_exists():
            if getattr(self, '_empty_state_frame', None):
                try: self._empty_state_frame.place_forget()
                except Exception: pass
            return
        if self._empty_state_frame:
            self._empty_state_frame.destroy()
        self._empty_state_frame = tk.Frame(self.root, bg=C["bg_root"])
        self._empty_state_frame.pack(fill="both", expand=True)
        # Use a centered inner frame — defer placement until geometry is known (fix #1)
        frm_center = tk.Frame(self._empty_state_frame, bg=C["bg_root"])
        self.root.update_idletasks()
        frm_center.place(relx=0.5, rely=0.5, anchor="center")
        lbl = tk.Label(frm_center, text="No hay ninguna carpeta configurada.", bg=C["bg_root"], fg=C["fg_sub"], font=("Segoe UI", 12))
        lbl.pack(pady=(0, 20))
        
        btn_add = tk.Label(frm_center, text=" Seleccionar carpeta a traquear ", bg=C["border_active"], fg="#fff", font=("Segoe UI", 12, "bold"), cursor="hand2", padx=20, pady=10)
        btn_add.pack()
        
        def _add_first():
            from tkinter import filedialog
            ruta = filedialog.askdirectory(title="Seleccionar Carpeta de Anime")
            if ruta:
                self.settings.add_carpeta(ruta)
                self.cambiar_carpeta_activa(ruta)
                
        btn_add.bind("<Button-1>", lambda e: _add_first())


    def _cfg_window(self):
        self.root.title(f"  {APP_TITLE}  v{APP_VERSION}")
        try:
            import sys
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "logo.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
        self.root.geometry("960x680")
        self.root.minsize(660, 480)
        self.root.configure(bg=C["bg_root"])
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = 960, 680
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        for k in ("<Up>", "<Down>", "<Left>", "<Right>", "<Return>"):
            self.root.bind(k, self._on_key_press)
        self.root.bind("<Button-1>", self._on_global_click, add="+")

    # ── UI build ─────────────────────────────────────────────────────────────

    def _toggle_folder_manager(self):
        import tkinter as tk
        from tkinter import filedialog
        
        # Check if already open
        if hasattr(self, '_fm_frame') and self._fm_frame and self._fm_frame.winfo_exists():
            self._fm_frame.destroy()
            self._fm_frame = None
            if self.directorio:
                self._outer.pack(fill="both", expand=True)
            else:
                self._show_empty_state()
            return
            
        # Hide current views (fix #4: always hide empty state when opening manager)
        if getattr(self, '_outer', None): self._outer.pack_forget()
        if self._empty_state_frame:
            self._empty_state_frame.pack_forget()
            try: self._empty_state_frame.place_forget()
            except Exception: pass
        
        self._fm_frame = tk.Frame(self.root, bg=C["bg_root"])
        self._fm_frame.pack(fill="both", expand=True)
        
        # Title and Top Bar
        hdr = tk.Frame(self._fm_frame, bg=C["bg_header"])
        hdr.pack(fill="x")
        
        btn_back = tk.Label(hdr, text=" \u2b05 Volver ", bg=C["bg_btn"], fg=C["fg_btn"], font=("Segoe UI", 10, "bold"), cursor="hand2", padx=10, pady=5)
        btn_back.pack(side="left", padx=20, pady=10)
        btn_back.bind("<Button-1>", lambda e: self._toggle_folder_manager())
        btn_back.bind("<Enter>", lambda e: e.widget.configure(bg=C["bg_btn_hover"]))
        btn_back.bind("<Leave>", lambda e: e.widget.configure(bg=C["bg_btn"]))
        
        tk.Label(hdr, text="Gestor de Trackers", font=("Segoe UI", 14, "bold"), bg=C["bg_header"], fg=C["fg_title"]).pack(side="left", pady=15, padx=10)
        
        # Add button (Prominent)
        btn_add = tk.Label(self._fm_frame, text=" + Añadir carpeta a traquear ", bg=C["border_active"], fg="#ffffff", font=("Segoe UI", 10, "bold"), cursor="hand2", pady=8)
        btn_add.pack(fill="x", padx=40, pady=15)
        
        def add_new():
            ruta = filedialog.askdirectory(title="Seleccionar Carpeta de Anime")
            if ruta:
                self.settings.add_carpeta(ruta)
                self.cambiar_carpeta_activa(ruta)
                self._toggle_folder_manager() # close and refresh
                
        btn_add.bind("<Button-1>", lambda e: add_new())
        
        # List frame
        self.folder_list_frame = tk.Frame(self._fm_frame, bg=C["bg_root"])
        self.folder_list_frame.pack(fill="both", expand=True, padx=40, pady=10)
        self._draw_folder_list()
        
    def _draw_folder_list(self):
        for w in self.folder_list_frame.winfo_children():
            w.destroy()
            
        carpetas = self.settings.carpetas_seguidas
        activa = self.settings.carpeta_activa
        
        if not carpetas:
            tk.Label(self.folder_list_frame, text="No sigues ninguna carpeta aún.", bg=C["bg_root"], fg=C["fg_sub"], font=("Segoe UI", 10)).pack(pady=20)
        else:
            for c in carpetas:
                is_active = (c == activa)
                bg_row = C["bg_card_hover"] if is_active else C["bg_card"]
                fg_row = C["fg_title"] if is_active else C["fg_normal"]
                
                row = tk.Frame(self.folder_list_frame, bg=bg_row, bd=1, relief="solid", cursor="hand2")
                row.pack(fill="x", pady=2)
                
                lbl = tk.Label(row, text=c, bg=bg_row, fg=fg_row, font=("Segoe UI", 9), cursor="hand2")
                lbl.pack(side="left", padx=10, pady=6)
                
                # Make the row and label clickable
                row.bind("<Button-1>", lambda e, ruta=c: self._activate_folder_from_manager(ruta))
                lbl.bind("<Button-1>", lambda e, ruta=c: self._activate_folder_from_manager(ruta))
                
                # Hover effect for the row
                def _on_enter(e, w=row, w2=lbl, is_act=is_active):
                    if not is_act:
                        w.configure(bg=C["bg_card_hover"])
                        w2.configure(bg=C["bg_card_hover"])
                def _on_leave(e, w=row, w2=lbl, original_bg=bg_row):
                    w.configure(bg=original_bg)
                    w2.configure(bg=original_bg)
                row.bind("<Enter>", _on_enter)
                row.bind("<Leave>", _on_leave)
                lbl.bind("<Enter>", _on_enter)
                lbl.bind("<Leave>", _on_leave)
                
                def make_btn(parent, text, color, cmd):
                    b = tk.Label(parent, text=text, bg=color, fg="#fff", font=("Segoe UI", 8, "bold"), cursor="hand2", padx=6, pady=2)
                    b.pack(side="right", padx=5, pady=6)
                    b.bind("<Button-1>", lambda e, c=cmd: c())
                    return b
                    
                make_btn(row, "X", "#DC143C", lambda p=c: self._remove_folder_from_manager(p))
                make_btn(row, "Abrir", C["bg_btn"], lambda p=c: os.startfile(p))
                if not is_active:
                    make_btn(row, "Activar", C["border_active"], lambda p=c: self._activate_folder_from_manager(p))
                else:
                    tk.Label(row, text=" (Activo) ", bg=C["border_active"], fg="#fff", font=("Segoe UI", 8, "bold")).pack(side="left", padx=10)

    def _activate_folder_from_manager(self, ruta):
        self.settings.set_carpeta_activa(ruta)
        self.cambiar_carpeta_activa(ruta)
        self._toggle_folder_manager()
        
    def _remove_folder_from_manager(self, ruta):
        import tkinter.messagebox as messagebox
        import os
        
        if messagebox.askyesno("Confirmar", f"¿Dejar de traquear esta carpeta?\n{ruta}"):
            # 1. Eliminar físicamente el archivo de progreso del disco de forma segura
            tracker_file = os.path.join(ruta, ".tracker.json")
            try:
                if os.path.exists(tracker_file):
                    os.remove(tracker_file)
            except Exception:
                pass
            
            # 2. Remover del gestor de rutas
            self.settings.remove_carpeta(ruta)
            
            # 3. Actualizar la interfaz si la carpeta eliminada era la activa
            if self.directorio == ruta:
                nueva_activa = self.settings.carpeta_activa
                self.cambiar_carpeta_activa(nueva_activa)
                
            # 4. Refrescar la vista del gestor de forma segura
            if hasattr(self, '_fm_frame') and self._fm_frame and self._fm_frame.winfo_exists():
                if hasattr(self, 'folder_list_frame'):
                    self._draw_folder_list()
                    self.root.update_idletasks()

    def _build_ui(self):
        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self):
        frm = tk.Frame(self.root, bg=C["bg_header"])
        frm.pack(fill="x", side="top")
        self._hdr_frm = frm

        self._accent = tk.Frame(frm, bg=C["border_active"], height=3)
        self._accent.pack(fill="x")

        inner = tk.Frame(frm, bg=C["bg_header"])
        inner.pack(fill="x", padx=18, pady=11)
        self._inner_hdr = inner

        self._lbl_icon = tk.Label(inner, text="\u25b6",
                                  font=("Segoe UI", 22),
                                  bg=C["bg_header"], fg=C["border_active"])
        self._lbl_icon.pack(side="left", padx=(0, 12))

        tf = tk.Frame(inner, bg=C["bg_header"])
        tf.pack(side="left", fill="y")
        self._tf = tf
        name = os.path.basename(self.directorio) or self.directorio
        self._lbl_name = tk.Label(tf, text=name,
                                  font=("Segoe UI", 13, "bold"),
                                  bg=C["bg_header"], fg=C["fg_title"], anchor="w")
        self._lbl_name.pack(anchor="w")
        self._lbl_path = tk.Label(tf, text=self.directorio,
                                  font=("Segoe UI", 8),
                                  bg=C["bg_header"], fg=C["fg_sub"], anchor="w")
        self._lbl_path.pack(anchor="w")

        bf = tk.Frame(inner, bg=C["bg_header"])
        bf.pack(side="right")
        self._bf = bf

        b1 = self._mkbtn(bf, "  Trackers  ",   self._toggle_folder_manager)
        b2 = self._mkbtn(bf, "  Refrescar  ", self._on_refresh)
        b3 = self._mkbtn(bf, "\u2699 Config", self._open_config)

        import tkinter.ttk as ttk
        
        # 3 View Selector Buttons
        v_frm = tk.Frame(bf, bg=C["bg_btn"], bd=0, highlightthickness=0)
        self._btn_v_tarj = tk.Label(v_frm, text="\u25a3", font=("Segoe UI", 11), cursor="hand2", bg=C["bg_btn"], fg=C["fg_btn"], padx=8, pady=2)
        self._btn_v_mos  = tk.Label(v_frm, text="\u229e", font=("Segoe UI", 11), cursor="hand2", bg=C["bg_btn"], fg=C["fg_btn"], padx=8, pady=2)
        self._btn_v_list = tk.Label(v_frm, text="\u2630", font=("Segoe UI", 11), cursor="hand2", bg=C["bg_btn"], fg=C["fg_btn"], padx=8, pady=2)
        
        self._btn_v_list.bind("<Button-1>", lambda e: self._set_vista("lista"))
        self._btn_v_mos.bind("<Button-1>",  lambda e: self._set_vista("mosaicos"))
        self._btn_v_tarj.bind("<Button-1>", lambda e: self._set_vista("tarjetas"))
        
        for w in (self._btn_v_list, self._btn_v_mos, self._btn_v_tarj):
            w.bind("<Enter>", lambda e, w=w: w.configure(bg=C["bg_btn_hover"]) if w.cget("bg") != C["border_active"] else None)
            w.bind("<Leave>", lambda e, w=w: w.configure(bg=C["bg_btn"]) if w.cget("bg") != C["border_active"] else None)
        
        self._btn_v_tarj.pack(side="right", padx=1)
        self._btn_v_mos.pack(side="right", padx=1)
        self._btn_v_list.pack(side="right", padx=1)
        
        b1.pack(side="right", padx=(10, 0))
        b2.pack(side="right", padx=(6, 0))
        b3.pack(side="right", padx=(6, 0))
        v_frm.pack(side="right", padx=(6, 0), pady=4)
        
        self._btns = [b1, b2, b3]
        self._v_btns = {"lista": self._btn_v_list, "mosaicos": self._btn_v_mos, "tarjetas": self._btn_v_tarj}
        self._update_v_btns()

        self._sep1 = tk.Frame(frm, bg=C["separator"], height=1)
        self._sep1.pack(fill="x")

        pf = tk.Frame(frm, bg=C["bg_header"], pady=5)
        pf.pack(fill="x", padx=18)
        self._pf = pf
        self.lbl_prog = tk.Label(pf, text="Cargando...",
                                 font=("Segoe UI", 9),
                                 bg=C["bg_header"], fg=C["fg_sub"])
        self.lbl_prog.pack(side="left")
        self.lbl_badge = tk.Label(pf, text="",
                                  font=("Segoe UI", 8, "bold"),
                                  bg=C["bg_header"], fg=C["badge_other"])
        self.lbl_badge.pack(side="right")

    def _build_content(self):
        outer = tk.Frame(self.root, bg=C["bg_root"], padx=12)
        outer.pack(fill="both", expand=True)
        self._outer = outer

        # ── List view container ────────────────────────────────────────────
        lc = tk.Frame(outer, bg=C["bg_root"])
        self._list_cont = lc

        ch = tk.Frame(lc, bg=C["bg_header"])
        ch.pack(fill="x")
        self._col_hdr = ch
        tk.Label(ch, text="   #", width=5, font=("Segoe UI", 8, "bold"),
                 bg=C["bg_header"], fg=C["fg_sub"], anchor="w"
                 ).pack(side="left", padx=(8, 0))
        tk.Label(ch, text="Archivo", font=("Segoe UI", 8, "bold"),
                 bg=C["bg_header"], fg=C["fg_sub"], anchor="w"
                 ).pack(side="left", padx=4, fill="x", expand=True)
        tk.Label(ch, text="Estado", width=28, font=("Segoe UI", 8, "bold"),
                 bg=C["bg_header"], fg=C["fg_sub"], anchor="e"
                 ).pack(side="right", padx=12)
        self._bline = tk.Frame(lc, bg=C["border"], height=1)
        self._bline.pack(fill="x")

        lf = tk.Frame(lc, bg=C["bg_list"])
        lf.pack(fill="both", expand=True)
        self._lframe = lf
        lc.bind("<Button-1>", lambda e, w=lc: self._force_focus(-1) if e.widget == w else None)
        lf.bind("<Button-1>", lambda e, w=lf: self._force_focus(-1) if e.widget == w else None)

        self._sb = tk.Scrollbar(lf, orient="vertical",
                                bg=C["bg_scrollbar"], troughcolor=C["bg_list"],
                                activebackground=C["border"], width=8,
                                relief="flat", bd=0)
        self._sb.pack(side="right", fill="y")

        focus_color = C.get("focus_border", "#FFD700")
        self.listbox = tk.Listbox(
            lf,
            selectmode=tk.SINGLE,
            exportselection=False,
            activestyle='none',
            highlightthickness=0,
            selectbackground=focus_color,    # Lee tu personalización (o usa #FFD700 por defecto)
            selectforeground="#000000",      # Color del texto al seleccionarse para que contraste bien
            bg=C["bg_list"], fg=C["fg_normal"],
            font=self.settings.fuente,
            yscrollcommand=self._sb.set,
            relief="flat", borderwidth=0
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self._sb.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", self._lb_dclick)
        self.listbox.bind("<ButtonRelease-1>", lambda e: self._force_focus(self.listbox.curselection()[0]) if self.listbox.curselection() else self._force_focus(-1))
        self.listbox.bind("<Return>",          self._lb_dclick)
        self.listbox.bind("<Motion>",          self._on_hover)
        self.listbox.bind("<Leave>",           self._on_leave)
        Tooltip(self.listbox, self._tooltip_text)

        # ── Card & Mosaicos views ──────────────────────────────────────────
        self._card_view = CardView(outer, self)
        self._mos_view  = MosaicosView(outer, self)

        # Show the correct initial view
        if self.settings.vista == "tarjetas":
            self._card_view.pack()
        elif self.settings.vista == "mosaicos":
            self._mos_view.pack()
        else:
            self._list_cont.pack(fill="both", expand=True)

    def _build_footer(self):
        self._fsep = tk.Frame(self.root, bg=C["border"], height=1)
        self._fsep.pack(fill="x", side="bottom")
        ft = tk.Frame(self.root, bg=C["bg_footer"], pady=6)
        ft.pack(fill="x", side="bottom")
        self._ft = ft
        self.lbl_status = tk.Label(
            ft,
            text=f"  {APP_TITLE} v{APP_VERSION}  -  Doble clic para reproducir",
            font=("Segoe UI", 8), bg=C["bg_footer"], fg=C["fg_sub"])
        self.lbl_status.pack(side="left", padx=8)
        self.lbl_total = tk.Label(ft, text="",
            font=("Segoe UI", 8, "bold"), bg=C["bg_footer"], fg=C["fg_sub"])
        self.lbl_total.pack(side="right", padx=12)

    # ── Vista toggle ──────────────────────────────────────────────────────────
    def _on_cb_change(self, event=None):
        val = self._vista_var.get()
        if "Lista" in val:      nueva = "lista"
        elif "Mosaicos" in val: nueva = "mosaicos"
        else:                   nueva = "tarjetas"
        if nueva != self._vista_actual:
            self._set_vista(nueva)

    def _set_vista(self, nueva):
        self._list_cont.pack_forget()
        self._card_view.pack_forget()
        self._mos_view.pack_forget()

        self._vista_actual = nueva
        self.settings.vista = nueva
        self._update_v_btns()
        self.root.after(50, self._apply_focus)

        if nueva == "lista":
            self._list_cont.pack(fill="both", expand=True)
            self._update_ui()
        elif nueva == "tarjetas":
            self._card_view.pack()
            self.root.update_idletasks()
            self._rebuild_cards()
            self._update_labels()
            self.root.after(50, self._apply_focus)
        elif nueva == "mosaicos":
            self._mos_view.pack()
            self.root.update_idletasks()
            self._rebuild_cards()
            self._update_labels()
            self.root.after(50, self._apply_focus)
            
        self.settings.save()

    def _update_v_btns(self):
        for k, b in self._v_btns.items():
            if k == self._vista_actual:
                b.configure(bg=C["border_active"], fg="#ffffff")
            else:
                b.configure(bg=C["bg_btn"], fg=C["fg_btn"])

    def _rebuild_cards(self):
        self.root.update_idletasks()
        if self._vista_actual == "tarjetas":
            self._card_view.rebuild(self.videos, self.directorio, self.ultimo_visto, self._thumb_cache)
        elif self._vista_actual == "mosaicos":
            self._mos_view.rebuild(self.videos, self.directorio, self.ultimo_visto, self._thumb_cache)

    def _on_thumb_ready(self, filepath):
        """Background thread callback — bounce to main thread safely."""
        self.root.after(0, lambda p=filepath: self._thumb_update_main(p))

    def _thumb_update_main(self, filepath):
        if self._vista_actual == "tarjetas" and self._card_view:
            self._card_view.update_thumbnail(filepath, self._thumb_cache)
        elif self._vista_actual == "mosaicos" and self._mos_view:
            self._mos_view.update_thumbnail(filepath, self._thumb_cache)

    # ── Button helper ─────────────────────────────────────────────────────────
    def _mkbtn(self, parent, text, cmd):
        b = tk.Label(parent, text=text, font=("Segoe UI", 8), cursor="hand2",
                     bg=C["bg_btn"], fg=C["fg_btn"], padx=10, pady=4, relief="flat")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>",    lambda e, w=b: w.configure(bg=C["bg_btn_hover"]))
        b.bind("<Leave>",    lambda e, w=b: w.configure(bg=C["bg_btn"]))
        return b

    def _tooltip_text(self, ev):
        idx = self.listbox.nearest(ev.y)
        if 0 <= idx < len(self.videos):
            ruta = os.path.join(self.directorio, self.videos[idx])
            size = ""
            try:
                b = os.path.getsize(ruta)
                size = (f"  {b/(1024**3):.2f} GB" if b >= 1024**3
                        else f"  {b/(1024**2):.1f} MB")
            except Exception:
                pass
            return f"{ruta}{size}"
        return ""

    # ── Hover (list mode) ─────────────────────────────────────────────────────
    def _on_hover(self, ev):
        idx = self.listbox.nearest(ev.y)
        if idx == self._hover_idx:
            return
        if self._hover_idx >= 0:
            self._row_style(self._hover_idx)
        self._hover_idx = idx
        if 0 <= idx < self.listbox.size():
            fn = self.videos[idx] if idx < len(self.videos) else ""
            if fn != self.ultimo_visto:
                self.listbox.itemconfig(idx, bg=C["bg_row_hover"])

    def _on_leave(self, _):
        if self._hover_idx >= 0:
            self._row_style(self._hover_idx)
            self._hover_idx = -1

    def _row_style(self, idx):
        if not (0 <= idx < self.listbox.size() and idx < len(self.videos)):
            return
        if idx == self._focus_index:
            self.listbox.itemconfig(idx, bg=C.get("focus_border", "#ffff00"), fg=C["bg_root"])
            return
        v = self.videos[idx]
        if v == self.ultimo_visto:
            if False:
                self.listbox.itemconfig(idx, bg=C["bg_row_active"], fg=C["fg_active"])
            else:
                self.listbox.itemconfig(idx, bg=C["bg_row_last"],   fg=C["fg_last"])
        else:
            self.listbox.itemconfig(
                idx,
                bg=C["bg_row_alt"] if idx % 2 else C["bg_row_normal"],
                fg=C["fg_normal"]
            )

    # ── Data ──────────────────────────────────────────────────────────────────
    def _refresh_videos(self):
        if not self.directorio or not __import__('os').path.isdir(self.directorio):
            self.videos = []
            return
        self.videos = sorted(
            [f for f in os.listdir(self.directorio)
             if os.path.splitext(f)[1].lower() in EXTS_VALIDAS],
            key=natural_sort_key
        )
        # Notificar al watcher la nueva lista
        if hasattr(self, '_watcher'):
            self._watcher.update_videos(self.videos, self.directorio)

    def _load_progress(self):
        """Carga el ultimo capitulo visto desde disco.
        Normaliza el atributo HIDDEN antes de leer para compatibilidad
        con OneDrive y rutas sincronizadas donde os.path.exists puede fallar.
        """
        import os, json, ctypes
        if not self.directorio: return ""
        ruta = os.path.join(self.directorio, ARCHIVO_REGISTRO)
        try:
            # os.path.isfile es mas robusto que os.path.exists para HIDDEN
            if not os.path.isfile(ruta):
                data = {"ultimo_visto": ""}
                with open(ruta, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                ctypes.windll.kernel32.SetFileAttributesW(str(ruta), 0x02)
                return ""
                
            # Quitar HIDDEN antes de leer
            ctypes.windll.kernel32.SetFileAttributesW(str(ruta), 0x80)
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Re-aplicar HIDDEN
            ctypes.windll.kernel32.SetFileAttributesW(str(ruta), 0x02)
            return data.get("ultimo_visto", "")
        except Exception:
            pass
        return ""

    def _save_progress(self, name):
        """Persiste el último capítulo visto en disco de forma robusta.
        

        Pasos:
        1. Quitar atributo HIDDEN antes de escribir (en Windows/OneDrive,
           escribir sobre un archivo HIDDEN falla silenciosamente).
        2. Leer JSON existente y actualizar solo 'ultimo_visto'.
        3. Escribir con fsync para garantizar escritura fisica al disco.
        4. Re-aplicar el atributo HIDDEN.
        """
        ruta = os.path.join(self.directorio, ARCHIVO_REGISTRO)
        FILE_ATTRIBUTE_NORMAL = 0x80
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            # Paso 1: quitar HIDDEN para poder escribir sin conflictos
            # Siempre intentar quitarlo porque os.path.exists falla en HIDDEN con OneDrive
            try:
                ctypes.windll.kernel32.SetFileAttributesW(str(ruta), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                pass

            # Paso 2: leer datos existentes
            data = {}
            if os.path.isfile(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["ultimo_visto"] = name

            # Paso 3: escribir con vaciado forzado al disco
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # Paso 4: re-aplicar HIDDEN
            ctypes.windll.kernel32.SetFileAttributesW(str(ruta), FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass

    # ── Render ────────────────────────────────────────────────────────────────
    def _update_ui(self):
        # Automatically hide empty state if we have a folder and videos
        if getattr(self, "_empty_state_frame", None):
            try:
                if self._empty_state_frame.winfo_exists():
                    if self.directorio and self.videos:
                        self._empty_state_frame.place_forget()
                        self._empty_state_frame.pack_forget()
            except Exception:
                pass

        if self._vista_actual == "tarjetas":
            self._card_view.update_states(self.ultimo_visto)
        elif self._vista_actual == "mosaicos":
            self._mos_view.update_states(self.ultimo_visto)
        else:
            self._update_list()
        self._update_labels()
        self.root.after(50, self._apply_focus)

    def _update_list(self):
        self.listbox.delete(0, tk.END)
        idx_uv = -1
        for idx, v in enumerate(self.videos):
            num = f"{idx+1:>3}"
            nc  = truncar(v, 55)
            if v == self.ultimo_visto:
                idx_uv = idx
                self.listbox.insert(tk.END,
                    f" {num}  \u2714  {nc:<56} [ULTIMO VISTO]")
                self.listbox.itemconfig(idx, bg=C["bg_row_last"], fg=C["fg_last"])
            else:
                self.listbox.insert(tk.END, f" {num}     {nc}")
                self.listbox.itemconfig(
                    idx,
                    bg=C["bg_row_alt"] if idx % 2 else C["bg_row_normal"],
                    fg=C["fg_normal"]
                )
        if idx_uv != -1:
            self.listbox.see(idx_uv)

    def _update_labels(self):
        total    = len(self.videos)
        self.lbl_total.config(text=f"{total} videos")
        
        # Check if empty state
        if not self.directorio:
            if hasattr(self, '_lbl_name') and hasattr(self, '_lbl_path'):
                self._lbl_name.config(text="")
                self._lbl_path.config(text="")
            if hasattr(self, 'lbl_prog'):
                self.lbl_prog.pack_forget()
            if hasattr(self, 'lbl_badge'):
                self.lbl_badge.pack_forget()
            return
            
        # Ensure they are packed if they were forgotten
        if hasattr(self, 'lbl_prog') and not self.lbl_prog.winfo_ismapped():
            self.lbl_prog.pack(side="left")
        if hasattr(self, 'lbl_badge') and not self.lbl_badge.winfo_ismapped():
            self.lbl_badge.pack(side="right")
            
        # Update header dynamically
        if hasattr(self, '_lbl_name') and hasattr(self, '_lbl_path'):
            import os
            name = os.path.basename(self.directorio) or self.directorio
            self._lbl_name.config(text=name)
            self._lbl_path.config(text=self.directorio)
            
        if total == 0:
            self.lbl_prog.config(text="No se encontraron videos en esta carpeta")
            self.lbl_badge.config(text="")
            return
            
        uv_idx = (self.videos.index(self.ultimo_visto)
                  if self.ultimo_visto in self.videos else -1)
        if uv_idx >= 0:
            pct = int((uv_idx + 1) / total * 100)
            self.lbl_prog.config(
                text=f"Progreso: capitulo {uv_idx+1} de {total}  ({pct}%)")
        else:
            self.lbl_prog.config(text=f"{total} videos encontrados")
        self.lbl_badge.config(text="")

    # ── Monitor (file-lock, respaldo) ─────────────────────────────────────────
    def _monitor(self):
        try:
            activo = None
            for v in self.videos:
                if esta_archivo_en_uso(os.path.join(self.directorio, v)):
                    activo = v
                    break
            if activo:
                if self.ultimo_visto != activo:
                    self.ultimo_visto = activo
                    self._save_progress(activo)
                    self._update_ui()
        except Exception:
            pass
        self.root.after(self.POLL_MS, self._monitor)

    # ── Auto-Sync por título de ventana ───────────────────────────────────────
    def _poll_sync_queue(self):
        """Revisa la cola del WindowWatcher cada 500ms desde el hilo principal.
        Thread-safe: nunca toca Tkinter desde otro hilo."""
        import queue
        try:
            detected = None
            while True:
                detected = self._sync_queue.get_nowait()
        except queue.Empty:
            pass

        if detected and detected != getattr(self, 'ultimo_visto', ''):
            self.ultimo_visto = detected
            self._save_progress(detected)
            
            def refrescar_ui():
                self._update_ui()
                short = truncar(detected, 38)
                self.root.update_idletasks()
                
            self.root.after(0, refrescar_ui)
        elif not detected:
            # Apagar indicador si no hay actividad reciente
            pass

        self.root.after(500, self._poll_sync_queue)

    def _flush_sync_queue(self):
        """Fuerza el vaciado de la cola del watcher sin bloqueos."""
        if not getattr(self, 'directorio', None):
            return
            
        import queue
        ultimo_detectado = None
        
        if hasattr(self, '_sync_queue'):
            try:
                while True:
                    ultimo_detectado = self._sync_queue.get_nowait()
            except queue.Empty:
                pass

        if ultimo_detectado and ultimo_detectado != getattr(self, 'ultimo_visto', ""):
            self.ultimo_visto = ultimo_detectado
            self._save_progress(ultimo_detectado)
        elif getattr(self, 'ultimo_visto', ""):
            self._save_progress(self.ultimo_visto)

    def _on_close(self):
        """Cierre limpio: lectura forzosa de emergencia, guardar progreso y parar el watcher."""
        self._flush_sync_queue()

        # Parar el hilo daemon
        try:
            if hasattr(self, '_watcher'):
                self._watcher.stop()
        except Exception:
            pass

        # Destruir la ventana
        self.root.destroy()


    # ── Actions ───────────────────────────────────────────────────────────────
    def _play_file(self, filename):
        ruta = os.path.join(self.directorio, filename)
        self.ultimo_visto = filename
        self._save_progress(filename)
        self._update_ui()
        if self._vista_actual == "lista" and filename in self.videos:
            self.listbox.selection_set(self.videos.index(filename))
        try:
            os.startfile(ruta)
        except Exception as exc:
            messagebox.showerror("Error al abrir",
                                 f"No se pudo abrir:\n{ruta}\n\n{exc}",
                                 parent=self.root)

    def _lb_dclick(self, _=None):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.videos):
            return
        self._play_file(self.videos[sel[0]])

    def _open_folder(self):
        try:
            os.startfile(self.directorio)
        except Exception:
            pass

    def _on_global_click(self, event):
        """Deselect focus (remove red border) when clicking outside video items."""
        w = event.widget
        # Walk up the widget tree to see if click landed on a video item
        while w:
            if getattr(w, "_is_video_item", False):
                return  # clicked ON a video item — keep focus
            if w is getattr(self, "listbox", None):
                return  # clicked on listbox — keep focus
            w = getattr(w, "master", None)
        # Clicked outside — clear focus
        if self._focus_index != -1:
            self._focus_index = -1
            self._apply_focus()

    def _on_key_press(self, event):
        if not self.videos: return
        k = event.keysym
        idx = self._focus_index
        if k == "Return":
            if 0 <= idx < len(self.videos):
                self._play_file(self.videos[idx])
            return

        ncols = 1
        if self._vista_actual == "mosaicos" and self._mos_view:
            ncols = getattr(self._mos_view, '_ncols', 1)
        elif self._vista_actual == "tarjetas" and self._card_view:
            ncols = getattr(self._card_view, '_ncols', 1)

        if self._vista_actual == "lista":
            if k == "Up": idx -= 1
            elif k == "Down": idx += 1
            elif k == "Left": idx -= 1
            elif k == "Right": idx += 1
        else:
            if k == "Left": idx -= 1
            elif k == "Right": idx += 1
            elif k == "Up": idx -= ncols
            elif k == "Down": idx += ncols

        idx = max(0, min(len(self.videos) - 1, idx))
        if idx != self._focus_index:
            self._focus_index = idx
            self._apply_focus()

    def _force_focus(self, idx):
        self._focus_index = idx
        self._apply_focus()
        
    def _apply_focus(self):
        if not self.videos: return
        idx = self._focus_index
        if self._vista_actual == "lista":
            self.listbox.selection_clear(0, tk.END)
            if idx >= 0:
                self.listbox.selection_set(idx)
                self.listbox.see(idx)
                self.listbox.activate(idx)
            # Re-draw list colors based on focus
            for i in range(len(self.videos)):
                if i == idx:
                    self.listbox.itemconfig(i, bg=C.get("focus_border", "#ffff00"), fg=C["bg_root"])
                else:
                    if self.videos[i] == self.ultimo_visto:
                            self.listbox.itemconfig(i, bg=C["bg_row_last"], fg=C["fg_last"])
                    else:
                        self.listbox.itemconfig(i, bg=C["bg_row_alt"] if i % 2 else C["bg_row_normal"], fg=C["fg_normal"])
        elif self._vista_actual == "mosaicos" and self._mos_view:
            if hasattr(self._mos_view, 'set_focus'):
                self._mos_view.set_focus(idx)
        elif self._vista_actual == "tarjetas" and self._card_view:
            if hasattr(self._card_view, 'set_focus'):
                self._card_view.set_focus(idx)

    def _open_config(self):
        VentanaConfiguracion(self.root, self)

    def _on_refresh(self):
        self._refresh_videos()
        if self._vista_actual in ("tarjetas", "mosaicos"):
            self._rebuild_cards()
        self._update_ui()
        self.lbl_status.config(text=f"  Refrescado - {len(self.videos)} videos")
        self.root.after(3000, lambda: self.lbl_status.config(
            text=(f"  {APP_TITLE} v{APP_VERSION}  -  "
                  "Doble clic para reproducir")))

    # ── Full theme re-apply (called from config window Guardar/Restablecer) ──
    def _apply_theme_all(self):
        self.root.configure(bg=C["bg_root"])

        # Header
        for w in [self._hdr_frm, self._inner_hdr, self._tf, self._pf, self._bf]:
            if w:
                w.configure(bg=C["bg_header"])
        self._accent.configure(bg=C["border_active"])
        self._sep1.configure(bg=C["separator"])
        self._lbl_icon.configure(bg=C["bg_header"], fg=C["border_active"])
        self._lbl_name.configure(bg=C["bg_header"], fg=C["fg_title"])
        self._lbl_path.configure(bg=C["bg_header"], fg=C["fg_sub"])
        self.lbl_prog.configure(bg=C["bg_header"], fg=C["fg_sub"])
        self.lbl_badge.configure(bg=C["bg_header"])
        for b in self._btns:
            try:
                b.configure(bg=C["bg_btn"], fg=C["fg_btn"])
            except Exception:
                pass

        # List
        self._outer.configure(bg=C["bg_root"])
        self._list_cont.configure(bg=C["bg_root"])
        self._col_hdr.configure(bg=C["bg_header"])
        for ch in self._col_hdr.winfo_children():
            if isinstance(ch, tk.Label):
                ch.configure(bg=C["bg_header"], fg=C["fg_sub"])
        self._bline.configure(bg=C["border"])
        self._lframe.configure(bg=C["bg_list"])
        self._sb.configure(bg=C["bg_scrollbar"], troughcolor=C["bg_list"])
        # FIX: re-apply font immediately on listbox after settings save
        self.listbox.configure(
            bg=C["bg_list"], fg=C["fg_normal"],
            selectbackground=C.get("focus_border", "#FFD700"),
            selectforeground="#000000",
            font=self.settings.fuente,        # bold + updated size
        )

        # Cards
        if self._card_view:
            self._card_view.apply_theme()

        # Footer
        self._fsep.configure(bg=C["border"])
        self._ft.configure(bg=C["bg_footer"])
        self.lbl_status.configure(bg=C["bg_footer"], fg=C["fg_sub"])
        self.lbl_total.configure(bg=C["bg_footer"], fg=C["fg_sub"])

        # Propagate theme to view-selector button container
        try:
            for w in (self._btn_v_list, self._btn_v_mos, self._btn_v_tarj):
                current = w.cget("bg")
                if current != C["border_active"]:  # don\'t repaint active btn
                    w.configure(bg=C["bg_btn"], fg=C["fg_btn"])
        except Exception:
            pass

        # Rebuild empty state frame with new theme colors if visible
        if getattr(self, "_empty_state_frame", None) and self._empty_state_frame.winfo_exists():
            self._show_empty_state()

        if self._mos_view: self._mos_view.apply_theme()

        # FIX: Immediately rebuild the active view with new colors/font
        if self._vista_actual in ("tarjetas", "mosaicos"):
            self._rebuild_cards()
        self._update_ui()


# ---------------------------------------------------------------------------
#  ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app  = VideoTrackerApp(root)
    root.mainloop()

<div align="center">

# 🎌 Anime & Video Tracker

**Aplicación de escritorio minimalista y moderna para la gestión y seguimiento de episodios de anime y videos locales.**

Desarrollada con **Python + Tkinter** · Diseño en **modo oscuro** · Paleta de acentos **carmesí** `#DC143C`

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange?style=flat-square)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=flat-square&logo=windows)
![Version](https://img.shields.io/badge/Versión-1.1.0-crimson?style=flat-square)

</div>

---

## ⚡ Descarga Rápida (Sin instalar nada)

> **¿Solo quieres usar la aplicación sin instalar nada?**
> Ve a la sección de **[Releases](../../releases)** a la derecha de este repositorio y descarga la última versión de **`AnimeTracker.exe`**.
>
> Es un ejecutable **100% portátil** — solo descárgalo y ejecútalo. No necesitas Python ni ninguna dependencia adicional.

---

## ✨ Características Principales

| Característica | Detalle |
|---|---|
| 🎨 **Interfaz Minimalista** | Paleta estricta de negro `#000000`, blanco `#FFFFFF` y carmesí `#DC143C` |
| 👁️ **Indicador de Último Visto** | Acento ámbar cálido `#FFB703` para identificar de un vistazo el último capítulo visto |
| 🗂️ **Tres Vistas** | Lista, Tarjetas y Mosaicos para organizar tu biblioteca como prefieras |
| 🔄 **Auto-Sync inteligente** | Detecta automáticamente qué episodio reproduces en VLC, MPC-HC, PotPlayer, etc. |
| ⚙️ **Panel de Configuración Integrado** | Personaliza colores y preferencias directamente desde la app |
| 📦 **100% Portátil** | Un solo `.exe` sin instaladores, sin dependencias externas |
| 🌙 **Modo Oscuro / Claro** | Cambia de tema con un clic |
| 🖼️ **Carga de Carátulas** | Asigna imágenes personalizadas a cada serie o carpeta de video |

---

## 🔄 Auto-Sync — Cómo funciona

AnimeTracker v1.1.0 incluye un **monitor de ventana activa** que detecta automáticamente qué episodio estás viendo:

1. Un hilo daemon (`WindowWatcher`) lee el título de la ventana en primer plano cada 2.5 segundos usando `ctypes` puro (sin dependencias externas).
2. Aplica patrones regex para extraer el número de episodio del título:
   - `VLC - Naruto - 08 - [720p].mkv` → detecta ep **8** ✅
   - `MPC-HC - One Piece E042.mkv` → detecta ep **42** ✅
   - `Attack on Titan S02E05 [1080p]` → detecta ep **5** ✅
3. Actualiza el indicador **ámbar (último visto)** automáticamente y guarda el progreso.
4. El indicador `⬤ Sync` en el footer se pone verde cuando detecta un cambio.
5. **CPU al 0%** cuando no hay reproductor activo.

---

## 🛠️ Tecnologías y Librerías

- **Python 3.10+** — Lenguaje principal
- **Tkinter** — Interfaz gráfica nativa
- **OpenCV (cv2)** — Procesamiento de video/miniaturas
- **Pillow (PIL)** — Manejo y redimensionado de imágenes
- **PyInstaller** — Empaquetado del ejecutable portátil
- **ctypes / windll.user32** — Detección nativa de ventana activa (sin pip)

---

## 🚀 Instrucciones de Uso

### Opción A — Ejecutable Portátil (Recomendado)

1. Ve a **[Releases](../../releases)** en este repositorio.
2. Descarga `AnimeTracker.exe` de la versión **v1.1.0**.
3. Cópialo a la carpeta con tus videos y ejecútalo. **¡Listo!**

### Opción B — Ejecutar desde el Código Fuente

```
git clone https://github.com/svkenier/animeVideoTraker.git
cd animeVideoTraker
python -m venv .venv
.venv\Scripts\activate
pip install pillow opencv-python
python anime_tracker.py
```

### Opción C — Compilar tu propio ejecutable

```
pyinstaller --onefile --windowed --icon=logo.ico --add-data "logo.svg;." --add-data "logo.ico;." --name AnimeTracker anime_tracker.py
```

---

## 📁 Estructura del Proyecto

```
animeVideoTraker/
├── anime_tracker.py      # Código fuente principal
├── logo.svg              # Icono vectorial del proyecto
├── logo.ico              # Icono para el ejecutable Windows
├── logo.png              # Versión PNG del logo
├── build_exe.bat         # Script de compilación rápida
├── AnimeTracker.spec     # Configuración de PyInstaller
└── README.md             # Este archivo
```

---

## 📋 Changelog

### v1.1.0
- ✅ Auto-Sync: detección automática de episodio por título de ventana activa
- ✅ WindowWatcher daemon thread — 0% CPU en reposo
- ✅ Indicador `⬤ Sync` en el footer (verde al detectar, gris en reposo)
- ✅ Compatible con VLC, MPC-HC, PotPlayer, KMPlayer, MPV y más
- ✅ Cierre limpio del hilo al cerrar la app

### v1.0.0
- ✅ Versión inicial: Lista, Tarjetas y Mosaicos
- ✅ Paleta negro/blanco/carmesí `#DC143C`
- ✅ Indicador ámbar `#FFB703` de último visto
- ✅ File-lock monitor, miniaturas, panel de config

---

Hecho con ❤️ — **AnimeTracker** by svkenier

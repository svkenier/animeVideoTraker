<div align="center">

# 🎌 Anime & Video Tracker

**Aplicación de escritorio minimalista y moderna para la gestión y seguimiento de episodios de anime y videos locales.**

Desarrollada con **Python + Tkinter** · Diseño en **modo oscuro** · Paleta de acentos **carmesí** `#DC143C`

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange?style=flat-square)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=flat-square&logo=windows)

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
| ⚙️ **Panel de Configuración Integrado** | Personaliza colores y preferencias directamente desde la app |
| 📦 **100% Portátil** | Un solo `.exe` sin instaladores, sin dependencias externas |
| 🌙 **Modo Oscuro / Claro** | Cambia de tema con un clic |
| 🖼️ **Carga de Carátulas** | Asigna imágenes personalizadas a cada serie o carpeta de video |

---

## 🛠️ Tecnologías y Librerías

- **Python 3.10+** — Lenguaje principal
- **Tkinter** — Interfaz gráfica nativa
- **OpenCV (cv2)** — Procesamiento de video/miniaturas
- **Pillow (PIL)** — Manejo y redimensionado de imágenes
- **PyInstaller** — Empaquetado del ejecutable portátil

---

## 🚀 Instrucciones de Uso

### Opción A — Ejecutable Portátil (Recomendado)

1. Ve a **Releases** en este repositorio.
2. Descarga `AnimeTracker.exe` de la última versión.
3. Ejecuta el archivo. **¡Listo!** No requiere instalación.

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
pyinstaller --onefile --windowed --icon=logo.ico --add-data "logo.svg;." --name AnimeTracker anime_tracker.py
```

El ejecutable resultante estará en la carpeta `dist/`.

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

Hecho con ❤️ — **AnimeTracker** by svkenier


<div align="center">

# 🎌 Anime & Video Tracker

**Aplicación de escritorio minimalista y moderna para la gestión y seguimiento de episodios de anime y videos locales.**

Desarrollada con **Python + Tkinter** · Diseño en **modo oscuro y claro** · Paleta de colores personalizable

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange?style=flat-square)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=flat-square&logo=windows)
![Version](https://img.shields.io/badge/Versión-3.1.0-crimson?style=flat-square)

</div>

---

## ⚡ Descarga Rápida (Sin instalar nada)

> **¿Solo quieres usar la aplicación sin instalar nada?**
> Ve a la sección de **[Releases](../../releases)** a la derecha de este repositorio y descarga la última versión de **`AnimeTracker.exe`**.
>
> Es un ejecutable **100% portátil** — solo descárgalo y ejecútalo. No necesitas Python ni dependencias adicionales.

---

## ✨ Características Principales

| Característica | Detalle |
|---|---|
| 🗂️ **Gestor de Carpetas** | Maneja múltiples series y directorios desde una sola interfaz centralizada. |
| 🎨 **Interfaz Dinámica** | Modos Oscuro/Claro integrados, con colores personalizados y sincronización en tiempo real. |
| 👁️ **Indicador de Último Visto** | Marca visual clara (✔) para identificar rápidamente por dónde te quedaste. |
| 🖼️ **Tres Vistas** | Visualiza tus episodios en formato Lista, Tarjetas detalladas o Mosaicos compactos. |
| 🔄 **Seguimiento Seguro** | Almacenamiento portátil y estructurado en la carpeta `AppData` para proteger tu progreso. |
| 📦 **100% Portátil** | Un solo ejecutable sin instaladores, scripts adicionales ni archivos temporales sueltos. |

---

## 📋 Historial de Versiones (Changelog)

El desarrollo del proyecto se consolida en dos grandes hitos, cada uno orientado a una filosofía de uso distinta:

### v3.1.0 (Versión Actual / Recomendada)
*Representa la línea principal, depurada y definitiva del proyecto.*

- **Buscador en tiempo real:** Filtra al instante la lista de animes desde el gestor de trackers (con diseño optimizado de alto contraste).
- **Sistema de Favoritos (⭐):** Estrellas interactivas con color personalizable desde la configuración.
- **Limpieza visual:** Interfaz del Gestor de Trackers completamente pulida (sin miniaturas acumuladas o layouts cortados).
- **Robustez técnica (Logs):** Sistema de registro de errores silencioso (`try...except`) que guarda todo en `%APPDATA%\AnimeTracker\app.log`.
- **Gestor de Trackers centralizado:** Capacidad para seguir, gestionar y alternar entre múltiples carpetas desde una única interfaz global.
- **Almacenamiento seguro en AppData:** Las configuraciones globales y el progreso se almacenan limpiamente en el perfil del usuario, garantizando persistencia portátil sin ensuciar los directorios de medios.
- **Sincronización impecable de temas:** Cambio instantáneo entre modo claro y oscuro en tiempo real, con redibujado automático y preciso de las tarjetas y mosaicos de video.
- **Corrección de interfaz (Cold Start):** Solución definitiva al centrado inicial de la aplicación, el estado vacío y el manejo de cabeceras de navegación.
- **Base de código depurada:** Estructura completamente refinada bajo estándares **PEP8** (Ruff) y código unificado sin rastros de archivos temporales.
- **Compatibilidad universal de reproductores:** Adaptada para funcionar con cualquier reproductor de vídeo externo sin depender de etiquetas o trackers intrusivos.

### v2.3 (Versión Clásica / Anterior)
*La experiencia tradicional enfocada al directorio aislado.*

- **Enfoque por carpeta:** Basada en el seguimiento estricto e individual de directorios específicos.
- **Uso directo:** Ideal para quienes prefieren colocar el ejecutable directamente dentro de la carpeta con los vídeos a gestionar de forma aislada.

---

## 🚀 Instrucciones de Uso (v3.1.0)

### Opción A — Ejecutable Portátil (Recomendado)

1. Ve a **[Releases](../../releases)** en este repositorio.
2. Descarga `AnimeTracker.exe` de la versión **v3.1.0**.
3. Ejecútalo en cualquier lugar de tu computadora. Desde la app, usa el **Gestor de Trackers** para añadir las carpetas donde guardas tus series o videos. **¡Listo!**

### Opción B — Ejecutar desde el Código Fuente

**Requisitos:** Python 3.10 o superior (solo librería estándar de Python, incluye Tkinter, ctypes, json, os, etc.). Opcionalmente puedes instalar `opencv-python` para una mejor extracción de miniaturas.

```bash
git clone https://github.com/svkenier/animeVideoTraker.git
cd animeVideoTraker
python -m venv .venv
.venv\Scripts\activate
pip install opencv-python   # Opcional, pero recomendado
python anime_tracker.py
```

### Opción C — Compilar tu propio ejecutable

Puedes generar el archivo `.exe` directamente usando PyInstaller:

```bash
pip install pyinstaller opencv-python
pyinstaller --onefile --windowed --icon=logo.ico --name AnimeTracker anime_tracker.py
```

*(Si utilizas el archivo AnimeTracker.spec, ejecuta: `pyinstaller AnimeTracker.spec`)*

---

## 🛡️ Sistema de Detección de Bloqueo de Antivirus

AnimeTracker cuenta con un sistema inteligente de detección de **falsos positivos / bloqueos** por parte de programas antivirus (como Windows Defender):

- **Alerta Modal Emergente:** Si el antivirus bloquea los permisos de escritura de la aplicación, el programa no se congelará ni cerrará abruptamente. En su lugar, interceptará el error de forma segura y mostrará una ventana emergente obligatoria, informándote claramente que el antivirus está impidiendo que se guarden tus progresos.
- **Barra de Estado Persistente:** Una vez que cierras la ventana de alerta, un banner rojo (bandera de estado) se mantendrá en la parte superior de la aplicación. Esto sirve como recordatorio permanente de que tus capítulos no se están guardando, para que puedas pausar y agregar la exclusión en tu antivirus o solucionar las restricciones de Windows ("Mark of the Web") y del directorio actual.

---

## 🛠️ Tecnologías y Librerías

- **Python 3.10+** — Lenguaje principal
- **Tkinter** — Interfaz gráfica nativa, sin dependencias complejas de terceros
- **OpenCV (cv2)** — Soporte avanzado para extracción de miniaturas (opcional)
- **ctypes / windll** — Integración profunda con Windows para miniaturas nativas del sistema operativo.
- **PyInstaller** — Construcción limpia y portátil

---

Hecho con ❤️ — **AnimeTracker** by svkenier

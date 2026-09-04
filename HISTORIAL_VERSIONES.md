# 📋 Historial de Versiones (Changelog)
## Actualizador de Programas de Windows

Todas las mejoras notables, nuevas funciones y correcciones de este proyecto están documentadas en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto sigue el versionado semántico [SemVer](https://semver.org/lang/es/).

---

## 🚀 [v1.2.0] — 04/09/2026
### ✨ Novedades
- **Desinstalación Oficial "Al Vuelo":**
  - Se agregó el botón rojo **`Quitar`** en la pestaña de *Actualizaciones Pendientes*.
  - Se añadió la columna **`Acción`** con botones individuales de **`Desinstalar`** en la pestaña *Todos los Programas Instalados* (cubriendo el catálogo completo de aplicaciones del sistema).
  - Integración nativa con `winget uninstall --id <id> --accept-source-agreements` para ejecutar el desinstalador oficial del fabricante.
- **Resolución de Conflictos de Instaladores:**
  - Capacidad para desinstalar versiones conflictivas (por ejemplo, cuando coexisten ejecutables legacy EXE y nuevos instaladores MSI en aplicaciones como `OpenMedia.4KVideoDownloaderPlus`).
- **Eliminación y Refresco Reactivo:**
  - Tras la desinstalación, el elemento se anima y se remueve en tiempo real de la interfaz, descontándose al instante de los contadores globales sin necesidad de recargar la página.
- **Renombrado Oficial del Repositorio en GitHub:**
  - El repositorio público se renombró oficialmente a: [**`actualizador-de-programas-de-windows`**](https://github.com/josedpdiaz/actualizador-de-programas-de-windows).

### 🎨 Mejoras de Interfaz (UI/UX)
- Nuevo modal de confirmación con diseño de advertencia/peligro (`btn-danger`) para prevenir desinstalaciones accidentales.
- Distintivo de versión (`v1.2.0`) visible tanto en la cabecera superior como en el pie de página de la aplicación.

---

## ⚡ [v1.1.0] — 04/09/2026
### ✨ Novedades
- **Actualización Selectiva por Casillas:**
  - Selección individual y múltiple de programas pendientes mediante casillas de verificación.
  - Botón de control dinámico **`Actualizar Seleccionados (X)`** con contador de elementos elegidos.
  - Opción de selección/deselección masiva con "Seleccionar todo".
- **Botón de Actualización Individual:**
  - Botón **`Actualizar`** en cada fila para actualizar un único programa de forma aislada.
- **Modal de Confirmación In-App:**
  - Sustitución de alertas nativas del navegador por ventanas modales integradas con diseño Glassmorphism, compatibles con el modo ventana independiente de Windows.

### 🐛 Correcciones
- **Codificación en Consola de Windows:**
  - Forzado de UTF-8 en salida estándar de Python para evitar fallos de codificación (CP1252) con caracteres especiales y emojis de estado.
- **Feedback Inmediato Post-Actualización:**
  - Distintivo verde brillante `✓ Actualizado` (`.row-just-updated`) y desvanecimiento suave (`.row-fading-out`) de 1.5s antes de retirar el programa de la lista.
  - Distintivo de advertencia `⚠ Revisar` (`.badge-updated-warning`) cuando el instalador requiere intervención o notifica incompatibilidad.

---

## 📦 [v1.0.0] — 04/09/2026
### ✨ Lanzamiento Inicial
- **Detección Automática de Software:**
  - Escaneo completo de los programas instalados en Windows y consulta a los repositorios de Microsoft (`winget`).
  - Detección precisa de versiones actuales y nuevas versiones disponibles.
- **Modo 1 Clic ("Actualizar Todo"):**
  - Ejecución silenciosa y desatendida de todas las actualizaciones disponibles con `winget upgrade --all --silent`.
- **Panel de Control con Glassmorphism:**
  - Interfaz moderna en modo oscuro, tarjetas de métricas (KPIs), buscador en tiempo real y selector de pestañas.
- **Consola de Terminal en Vivo:**
  - Monitorización en directo con streaming de logs, auto-scroll y distinción por niveles (información, proceso, éxito, error).
- **Lanzadores de Escritorio:**
  - Script `iniciar-silencioso.vbs` para arrancar sin ventanas negras de consola.
  - Generador de acceso directo en el Escritorio (`Crear-Acceso-Directo.ps1`).
  - Sincronización y publicación en repositorio de GitHub.

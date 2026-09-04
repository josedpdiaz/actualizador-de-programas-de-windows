# Actualizador de Programas de Windows ⚡ (v1.2.0)

Aplicación de escritorio moderna, ultraligera y eficiente para detectar todos los programas instalados en Windows, actualizarlos automáticamente a su última versión o desinstalarlos de forma oficial y al vuelo.

Desarrollada para ser **lo más sencilla, eficaz y rápida posible**, apoyándose directamente en el gestor oficial de Microsoft: **Windows Package Manager (`winget`)**.

> 📖 **¿Primera vez usando la herramienta?** Consulta el [**Manual de Puesta en Marcha Rápida**](MANUAL_PUESTA_EN_MARCHA.md).  
> 📋 **Historial de Versiones:** Consulta [**HISTORIAL_VERSIONES.md**](HISTORIAL_VERSIONES.md) para ver los cambios de cada versión.

---

## 🌟 Características Principales

- **Detección Automática Completa:** Escanea al instante el sistema e identifica qué aplicaciones tienen nuevas versiones disponibles en los repositorios oficiales de Microsoft.
- **⚡ Actualizar Todo con 1 Clic:** Actualización desatendida y silenciosa de todos los paquetes pendientes sin intervenciones repetitivas.
- **Actualización Selectiva:** Posibilidad de marcar o desmarcar programas específicos o usar el botón individual `Actualizar`.
- **🗑️ Desinstalación Oficial "Al Vuelo":** Botón `Quitar` en actualizaciones y `Desinstalar` en el catálogo completo para eliminar aplicaciones no deseadas o con conflictos de versión (ej. ejecutables antiguos vs nuevos MSI).
- **Búsqueda Instantánea:** Filtra por nombre de aplicación o ID de paquete en tiempo real.
- **Consola de Terminal en Vivo:** Visualiza el progreso exacto, descargas e instalación de cada instalador con registro de tiempo.
- **Modo Ventana de Escritorio:** Se abre como una aplicación de escritorio nativa e independiente sin barras de navegador ni pestañas innecesarias.
- **Cero Dependencias Pesadas:** Funciona con el entorno estándar de Python y librerías nativas, sin descargas pesadas de Electron de cientos de megabytes.

---

## 🚀 Cómo Iniciar la Aplicación

### Método 1 (Recomendado): Desde el Acceso Directo del Escritorio
Haz doble clic sobre el acceso directo **`Actualizador de Programas`** en tu Escritorio de Windows.

### Método 2: Doble clic silencioso
Haz doble clic en **`iniciar-silencioso.vbs`**. La aplicación se abrirá directamente en su propia ventana de escritorio sin que aparezca ninguna consola negra.

### Método 3: Con consola de depuración
Haz doble clic en **`iniciar.bat`**.

### Método 4: Restaurar acceso directo en el Escritorio
Haz clic derecho en **`Crear-Acceso-Directo.ps1`** y selecciona *Ejecutar con PowerShell*, o ejecuta:
```powershell
powershell -ExecutionPolicy Bypass -File .\Crear-Acceso-Directo.ps1
```

---

## 🛠️ Tecnologías Empleadas

- **Backend:** Python 3.12 (HTTP Server multihilo con `ReusableHTTPServer`, Subprocess stream, API REST, caché control `no-cache`).
- **Frontend:** HTML5 semántico, CSS3 con Glassmorphism (tema oscuro refinado), JavaScript vanilla reactivo con versionado de activos.
- **Motor del Sistema:** Windows Package Manager (`winget`).
- **Control de Versiones:** Git & GitHub CLI (`gh`).

---

## 📦 Repositorio Oficial en GitHub

- **URL:** [https://github.com/josedpdiaz/actualizador-de-programas-de-windows](https://github.com/josedpdiaz/actualizador-de-programas-de-windows)
- **Versión Actual:** `v1.2.0`
- **Autor:** Jose D. Díaz

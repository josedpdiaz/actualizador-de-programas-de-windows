# 03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS ⚡

Aplicación de escritorio moderna, ultraligera y eficiente para detectar todos los programas instalados en Windows y actualizarlos automáticamente a su última versión con un solo clic.

Desarrollada para ser **lo más sencilla, eficaz y rápida posible**, apoyándose directamente en el gestor oficial de Microsoft: **Windows Package Manager (`winget`)**.

> 📖 **¿Primera vez usando la herramienta?** Consulta el [**Manual de Puesta en Marcha Rápida (Paso a Paso)**](MANUAL_PUESTA_EN_MARCHA.md).

---

## 🌟 Características Principales

- **Detección Automática:** Escanea al instante el sistema e identifica qué aplicaciones tienen nuevas versiones disponibles en los repositorios oficiales de Windows y Microsoft Store.
- **⚡ Actualizar Todo con 1 Clic:** Actualización desatendida y silenciosa de todos los paquetes pendientes sin intervenciones repetitivas.
- **Actualización Selectiva:** Posibilidad de marcar o desmarcar programas específicos para actualizar solo los que necesites.
- **Búsqueda Instantánea:** Filtra por nombre de aplicación o ID de paquete en tiempo real.
- **Consola de Terminal en Vivo:** Visualiza el progreso exacto, descargas e instalación de cada instalador con registro de tiempo.
- **Modo Ventana de Escritorio:** Se abre como una aplicación de escritorio nativa e independiente sin barras de navegador ni pestañas innecesarias.
- **Cero Dependencias Pesadas:** Funciona con el entorno estándar de Python y librerías nativas, sin descargas pesadas de Node/Electron de cientos de megabytes.

---

## 🚀 Cómo Iniciar la Aplicación

### Método 1 (Recomendado): Doble clic silencioso
Haz doble clic en **`iniciar-silencioso.vbs`**. La aplicación se abrirá directamente en su propia ventana de escritorio sin que aparezca ninguna consola negra.

### Método 2: Con consola de depuración
Haz doble clic en **`iniciar.bat`**.

### Método 3: Crear acceso directo en el Escritorio
Haz clic derecho en **`Crear-Acceso-Directo.ps1`** y selecciona *Ejecutar con PowerShell*, o ejecuta en PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\Crear-Acceso-Directo.ps1
```
Aparecerá un acceso directo llamado **`Actualizador de Programas`** en tu Escritorio de Windows.

---

## 🛠️ Tecnologías Empleadas

- **Backend:** Python 3.12 (HTTP Server multihilo, Subprocess stream, API REST).
- **Frontend:** HTML5 semántico, CSS3 con Glassmorphism (tema oscuro refinado), JavaScript vanilla reactivo.
- **Motor del Sistema:** Windows Package Manager (`winget`).
- **Control de Versiones:** Git & GitHub CLI (`gh`).

---

## 📦 Repositorio en GitHub

- **URL:** [https://github.com/josedpdiaz/03-ia-actualizador-programas-windows](https://github.com/josedpdiaz/03-ia-actualizador-programas-windows)
- **Autor:** Jose D. Díaz

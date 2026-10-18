# Actualizador de Programas de Windows ⚡ (v1.4.0)

Aplicación de escritorio moderna, ultraligera y eficiente para detectar todos los programas instalados en Windows, actualizarlos automáticamente a su última versión o desinstalarlos de forma oficial y al vuelo.

Desarrollada para ser **lo más sencilla, eficaz y rápida posible**, apoyándose directamente en el gestor oficial de Microsoft: **Windows Package Manager (`winget`)**.

> 📖 **¿Primera vez usando la herramienta?** Consulta el [**Manual de Puesta en Marcha Rápida**](MANUAL_PUESTA_EN_MARCHA.md).  
> 📋 **Historial de Versiones:** Consulta [**HISTORIAL_VERSIONES.md**](HISTORIAL_VERSIONES.md) para ver los cambios de cada versión.

---

## 🌟 Características Principales

- **Detección Automática Completa:** Consulta WinGet y muestra las aplicaciones con actualizaciones detectadas. No todos los programas instalados están cubiertos por WinGet.
- **⚡ Actualizar Todo con 1 Clic:** Procesa uno a uno los programas de la lista, con tiempo transcurrido y resultado individual. Algunos instaladores necesitan autorización de Windows.
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
- **Versión Actual:** `v1.4.0`
- **Autor:** Jose D. Díaz

## Versión 1.4.0: actualizaciones con seguimiento

- Cola basada en la lista revisada, identificadores exactos y bloqueo de operaciones simultáneas.
- Resumen de actualizados, fallidos, no aplicables, reinicios y pendientes. Los fallos no se presentan como éxito general.
- Límite de 30 minutos por actualización y 2 minutos por escaneo. El tiempo transcurrido sigue visible aunque el instalador deje de escribir mensajes.
- No se fuerzan programas con versión desconocida ni se reinicia Windows automáticamente.
- Al abrir, los dos escaneos se ejecutan en orden. Ya no se fuerza el cierre de procesos ajenos para liberar el puerto.

### Permisos y modo administrador opcional

El inicio habitual conserva los permisos del usuario. Si vas a actualizar varios programas que requieren administrador, puedes ejecutar `iniciar-administrador.ps1` desde PowerShell: Windows solicitará elevación para esa sesión. Puede reducir avisos repetidos, pero depende de cada instalador y no garantiza eliminarlos. No cambia UAC ni crea tareas con privilegios permanentes. Si ya hay un servidor del actualizador abierto, el script lo indica y no cambia sus permisos; ciérralo antes de usar este modo.

Si se agota el tiempo, la cola se detiene y bloquea más instalaciones o desinstalaciones en esa sesión. Un instalador independiente puede seguir abierto: revísalo y espera a que termine, o reinicia Windows cuando corresponda, antes de reabrir el actualizador. No vuelvas a lanzar otra instalación a ciegas.

### Comprobar el proyecto

```powershell
python -m unittest discover -s tests -v
node tests/test_polling.js
python -m py_compile app.py update_engine.py
node --check web/app.js
```

Las pruebas no actualizan ni desinstalan programas reales. Se prueban procesos de espera reales y se simulan los resultados de WinGet. El rendimiento real depende de la red, del paquete y del instalador del fabricante.

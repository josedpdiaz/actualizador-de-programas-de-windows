# Revisión de actividad — versión 1.5

Alcance aprobado en la conversación: mostrar aplicaciones activas, facilitar su revisión en el Administrador de tareas y comprobar su estado al volver. El actualizador no termina procesos ni interpreta el consumo de CPU como ausencia de trabajo importante.

## Uso

1. Consulta el estado bajo el nombre de cada aplicación.
2. Si aparece En ejecución, pulsa Revisar en Administrador de tareas. Busca el nombre de proceso o PID indicado; la herramienta de Windows se abre sin seleccionar automáticamente un proceso.
3. Decide allí si dejarlo abierto o finalizarlo. Cerrar procesos puede perder trabajo o interrumpir servicios; el actualizador no ejecuta esa decisión.
4. Al volver, pulsa Comprobar actividad. Las aplicaciones que dejan de aparecer activas pueden marcarse para actualizar.

Sin actividad detectada significa que no se encontraron los procesos conocidos asociados a esa aplicación. Sin comprobar significa que no existe una asociación fiable o que falló la lectura de procesos. Ninguno garantiza que sea seguro actualizar. Las desconocidas quedan desmarcadas pero pueden seleccionarse manualmente tras revisarlas.

## Implementación y comprobación

- `activity.py`: asociaciones explícitas por nombre, consulta de procesos de Windows con límite de ocho segundos y caché de hasta cinco; apertura de Taskmgr.exe de Windows. Sin terminación de procesos.
- `app.py`: estados de las filas, validación al reservar la operación y comprobación antes de ejecutar cada paquete. La cola global solo incluye Sin actividad detectada.
- `web/activity-ui.js`: presentación de estados y selección conservadora; si una lectura pasa a desconocida, se desmarca al refrescar.
- `web/app.js`: botones de revisión y consulta, preservación de desmarcados manuales y advertencia para actualizaciones individuales sin comprobar.
- El instalador verifica que los nuevos archivos estén incluidos.

Pruebas: `python -m unittest discover -s tests -v`, `node tests/test_polling.js`, `node tests/test_activity_ui.js` y comprobaciones de sintaxis. Se verificaron procesos reales de Nextcloud y Tailscale en segundo plano y ausencia de proceso VLC. Vista de prueba con los tres estados y sin instalaciones habilitadas. La revisión independiente detectó y permitió corregir selección desconocida heredada y reactivación visual de un botón bloqueado.

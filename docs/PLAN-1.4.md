# Actualizador 1.4: alcance y verificación

Objetivo aprobado: mejorar el flujo existente de actualizaciones y publicar una nueva versión en el repositorio del usuario. Conservar la instalación anterior y sus cambios locales.

## Cambios

- [x] Supervisar procesos sin bloquear el control del tiempo cuando no producen salida. Prueba con un proceso real que duerme, sin instalar aplicaciones.
- [x] Reservar operaciones antes de lanzar hilos. Verificar dos peticiones HTTP concurrentes y rechazar orígenes ajenos.
- [x] Cola de identificadores exactos tomada de la lista mostrada. Validar entrada, deduplicar y no forzar versiones desconocidas.
- [x] Contabilizar éxitos, fallos, no aplicables, reinicios y pendientes. Detener la cola ante espera agotada o reinicio necesario.
- [x] Mostrar tiempo transcurrido y resumen final. Conservar los permisos de Windows y ofrecer un inicio administrativo opcional.
- [x] Revisar visualmente y comprobar distribución con el nuevo módulo incluido.
- [ ] Revisar código, publicar y comprobar versión remota.

## Límites

No actualizar aplicaciones reales durante las pruebas. No instalar controladores. No desactivar UAC ni reiniciar automáticamente. El modo silencioso depende del instalador. Una espera agotada detiene el cliente WinGet y bloquea nuevas mutaciones en esa sesión; un instalador independiente puede continuar y debe revisarse.

## Decisiones

La selección de mejoras fue aprobada en la conversación. Se trabaja en una copia clonada para preservar el instalador local modificado y los archivos de respaldo. No se rediseña la interfaz. Las pruebas de la cola simulan WinGet; las de supervisión usan procesos Python reales. La latencia real de descarga e instalación queda pendiente de una actualización real elegida por el usuario.

## Verificación

`python -m unittest discover -s tests -v`, `python -m py_compile app.py update_engine.py`, `node --check web/app.js`, revisión visual y revisión independiente del diff.

Revisión: corregidas cuatro observaciones de sincronización y progreso. Suite final: 14 pruebas Python y 3 comprobaciones de polling. Vista local con instalaciones desactivadas verificada.

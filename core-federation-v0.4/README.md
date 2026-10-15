# YO+ CORE Federation v0.4 — prototipo experimental

Servicio MCP independiente del controlador YO+ Continuity. Incluye core_submit, core_get y core_propose_edge. Registra transacciones en SQLite **solo cuando el volumen del host es persistente**.

**No desplegado ni conectado remotamente**. No exponer sin autenticación Bearer/OAuth validada. El alojamiento gratuito sin disco persistente no es adecuado para el expediente canónico.

Pruebas locales: python -m unittest discover -s tests -v

Pendientes: almacenamiento persistente remoto, control de acceso, backups, validación semántica independiente, concurrencia/carga, migraciones y llamadas comprobadas entre plugins. Este repositorio es público: no introducir secretos ni datos sensibles.
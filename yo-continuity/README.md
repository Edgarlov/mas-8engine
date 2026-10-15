# YO+ Continuity Controller — despliegue experimental

Rama separada del proyecto KBS-TECH. El contenido principal de `main` no se modifica.

Controlador propuesto: u=clip(0.3R+0.4E+0.3C-0.2P,0,1); riesgo nuevo=0.7*r_prev+0.3*u. Histéresis: explorar→recuperar cuando riesgo≥0.65; recuperar→explorar cuando riesgo≤0.30.

**No está desplegado ni conectado a ChatGPT.** Esta rama es un espacio de preparación. Un servicio remoto exige autenticación, persistencia y configuración de permisos. No se incluyen secretos ni datos personales. El repositorio es **público**.

La versión probada localmente se conserva también en el paquete ZIP preparado en la conversación. Antes de implementar MCP se necesita una base de datos persistente y control de acceso. No crear costes automáticamente.

# CONTROL-SISTEMA-POSTGRADO

Sistema Django para control de organización docente de postgrado.

## Despliegue en Railway

1. Crea un nuevo proyecto en Railway y conecta este repositorio de GitHub.
2. Agrega un servicio de PostgreSQL en el mismo proyecto.
3. En el servicio de la aplicación, configura estas variables:

```env
SECRET_KEY=una-clave-segura
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app,https://*.up.railway.app
DB_SSL_REQUIRE=False
```

Railway agrega `DATABASE_URL` automáticamente cuando conectas PostgreSQL.

Si la aplicación usa archivos subidos por usuarios, configura también `CLOUDINARY_URL`, porque el filesystem de Railway no debe usarse como almacenamiento persistente de media.

El proyecto incluye `Dockerfile` y `railway.json`; Railway construirá la imagen, ejecutará migraciones al iniciar y levantará Gunicorn.

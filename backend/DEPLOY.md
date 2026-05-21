# Guía de Despliegue — Sistema de Control de Entregas

## Cloud Run (Backend)

### Configuración recomendada (free tier)

    gcloud run deploy control-entregas-api \
      --source . \
      --region <region> \
      --platform managed \
      --allow-unauthenticated \
      --min-instances=0 \
      --max-instances=2 \
      --concurrency=80 \
      --memory=512Mi \
      --cpu=1 \
      --timeout=60 \
      --set-secrets=ENCRYPTION_KEY=encryption-key:latest,JWT_SECRET_KEY=jwt-secret:latest,ADMIN_PASSWORD=admin-password:latest,DATABASE_URL=database-url:latest \
      --set-env-vars=ENVIRONMENT=production,CORS_ORIGINS='["https://<dominio-frontend>"]',MAX_XML_UPLOAD_MB=1

### Notas

- `min-instances=0`: queda dentro del free tier de Cloud Run.
- `max-instances=2`: techo conservador, evita facturas sorpresa.
- El rate limit (auth_attempts) persiste en PostgreSQL, no en memoria —
  funciona correctamente con escala-a-cero y múltiples réplicas.
- Si en el futuro se escala más allá de 2 réplicas, revisar:
  - Concurrencia en la BD por los INSERT al rate_limit.
  - Posible migración a Redis si la latencia se vuelve un problema.

## Supabase (PostgreSQL)

### Habilitar pg_cron para cleanup automático de auth_attempts

**Una sola vez**, en el SQL Editor de Supabase:

    -- 1. Habilitar la extensión (si no está)
    CREATE EXTENSION IF NOT EXISTS pg_cron;

    -- 2. Programar el cleanup diario (3 AM UTC)
    SELECT cron.schedule(
        'cleanup-auth-attempts',
        '0 3 * * *',
        $$DELETE FROM auth_attempts WHERE created_at < now() - interval '24 hours'$$
    );

    -- 3. Verificar que quedó programado
    SELECT jobname, schedule, command FROM cron.job;

Para desprogramar:

    SELECT cron.unschedule('cleanup-auth-attempts');

## Política operativa

- **Mantener siempre al menos 2 usuarios admin activos.** Si solo hay un admin y se bloquea por intentos fallidos, queda sin acceso a la UI. Usar el script de emergencia (ver abajo) si ocurre.
- **Script de emergencia para desbloquear:**

      cd backend
      python scripts/unlock_user.py <email>

  Requiere acceso a la BD vía `DATABASE_URL` en el entorno.

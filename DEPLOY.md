# Deploy en Railway — Guía paso a paso

## 1. Crear cuenta en Railway
Ve a [railway.app](https://railway.app) → Sign up con GitHub.

## 2. Crear proyecto nuevo
New Project → Deploy from GitHub repo → selecciona `albertoiglesiascatalan-sudo/Insurtech`

## 3. Añadir servicios de base de datos
En el proyecto de Railway:
- **Add Service → Database → PostgreSQL** (Railway lo configura automático, da `DATABASE_URL`)
- **Add Service → Database → Redis** (da `REDIS_URL`)

Activa la extensión pgvector en PostgreSQL:
```
railway run --service postgres psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 4. Servicio API (FastAPI)
- Add Service → GitHub Repo → selecciona el repo
- Root Directory: `apps/api`
- Variables de entorno (Settings → Variables):

| Variable | Valor |
|---|---|
| `DATABASE_URL` | (auto, del servicio PostgreSQL de Railway) |
| `REDIS_URL` | (auto, del servicio Redis de Railway) |
| `OPENAI_API_KEY` | `sk-tu-clave-real` |
| `RESEND_API_KEY` | `re_tu-clave-real` |
| `RESEND_FROM_EMAIL` | `newsletter@tudominio.com` |
| `SECRET_KEY` | (genera con: `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `ENVIRONMENT` | `production` |
| `APP_URL` | URL del servicio web (p.ej. `https://insurtech-web.up.railway.app`) |
| `ADMIN_EMAIL` | `tu@email.com` |

## 5. Servicio Web (Next.js)
- Add Service → GitHub Repo → misma repo
- Root Directory: `apps/web`
- Variables de entorno:

| Variable | Valor |
|---|---|
| `NEXT_PUBLIC_API_URL` | URL del servicio API (p.ej. `https://insurtech-api.up.railway.app`) |
| `INTERNAL_API_URL` | igual que `NEXT_PUBLIC_API_URL` |
| `NEXTAUTH_URL` | URL del servicio web (p.ej. `https://insurtech-web.up.railway.app`) |
| `NEXTAUTH_SECRET` | (genera con: `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `GOOGLE_CLIENT_ID` | (opcional, de Google Cloud Console) |
| `GOOGLE_CLIENT_SECRET` | (opcional) |

## 6. Primer despliegue
Railway desplegará automáticamente al hacer push.
El comando de inicio ya corre las migraciones: `alembic upgrade head && uvicorn ...`

## 7. Crear primer admin
Una vez desplegado, desde Railway CLI o el panel:
```bash
railway run --service api python -m app.scripts.make_admin --email=tu@email.com
railway run --service api python -m app.scripts.seed_sources
railway run --service api python -m app.scripts.seed_articles
```

## 8. Google OAuth (opcional)
En [Google Cloud Console](https://console.cloud.google.com):
1. APIs & Services → Credentials → Create OAuth 2.0 Client
2. Authorized redirect URIs: `https://tu-web.up.railway.app/api/auth/callback/google`
3. Copia Client ID y Client Secret al `.env` de Railway

## Dominios personalizados
En Railway → Settings → Domains → Add Custom Domain
Actualiza `NEXTAUTH_URL`, `APP_URL` y las URIs de Google OAuth con tu dominio real.

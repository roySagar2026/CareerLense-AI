# Deployment guide

The recommended target is **one Vercel project** that serves the React build and the FastAPI backend (as a Python serverless function) on the same origin, backed by **Neon Postgres**. Same-origin matters: the refresh-token cookie is `SameSite=Lax`.

## 1. Create the database (Neon, free tier)

1. Create a project at neon.tech. Copy the **pooled** connection string (host contains `-pooler`), keep `?sslmode=require`.
2. Create the tables once from your machine:

   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   $env:DATABASE_URL = "<neon pooled connection string>"
   alembic upgrade head
   ```

   (Or set the `MIGRATION_DATABASE_URL` GitHub secret and the deploy workflow will run it for you.)

## 2. Push the code to GitHub

```powershell
git init; git add .; git commit -m "CareerLens AI"
git remote add origin https://github.com/<you>/careerlens-ai.git
git push -u origin main
```

Make sure `.env` is not committed (it is git-ignored).

## 3. Import into Vercel

1. vercel.com → Add New → Project → import the repository. Leave the root directory at the repo root. `vercel.json` already sets the install/build commands, output directory, API function and rewrites.
2. Environment variables (Project → Settings → Environment Variables), for Production and Preview:

   | Name | Value |
   |---|---|
   | `APP_ENV` | `production` |
   | `DATABASE_URL` | Neon pooled connection string |
   | `JWT_SECRET` | 32+ random characters (`./infrastructure/scripts/generate-secret.ps1`) |
   | `APP_BASE_URL` | your public URL, e.g. `https://careerlens.vercel.app` |
   | `MAX_UPLOAD_MB` | `4` |
   | `RESEND_API_KEY`, `EMAIL_FROM` | optional, enables password-reset emails |

   Leave `CORS_ORIGINS` empty (same origin).
3. Deploy. Then verify:

   ```bash
   bash infrastructure/scripts/smoke-test.sh https://<your-app>.vercel.app
   ```

   (Git Bash or WSL on Windows.) It checks `/api/health`, `/api/health/ready` and a register → login → refresh round trip, creating one throwaway user.

Limits to know about on Vercel: request bodies up to 4.5 MB (hence the 4 MB upload limit), function time 60 s, 250 MB function size (hence no spaCy / sentence-transformers).

## 4. Optional: GitHub Actions deployment

`deploy.yml` deploys `main` to a staging (preview) URL and `v*.*.*` tags to production, smoke-testing each. Add repository secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (from `vercel link` → `.vercel/project.json`), optionally `MIGRATION_DATABASE_URL` and `VERCEL_BYPASS_SECRET`. Create `staging` and `production` environments in GitHub and require reviewers on `production` for manual approval. If you use this route, disable Vercel's own Git auto-deploy to avoid double deployments.

## Netlify (frontend only)

Netlify Functions can't run this Python backend. You can host `frontend/` on Netlify (`netlify.toml` is provided) **only if** the API runs elsewhere (e.g. the Vercel project above). Uncomment the `/api/*` proxy redirect in `netlify.toml` and point it at the backend so the browser stays same-origin.

## Containers (any Docker host)

```bash
docker compose up --build                       # local stack
docker compose -f docker-compose.prod.yml --env-file .env up -d   # prebuilt GHCR images
```

Images are built by `docker-build.yml` (after frontend and backend CI pass), scanned with Trivy, and pushed to `ghcr.io/<owner>/careerlens-{backend,frontend}`. Put TLS in front of nginx: with `APP_ENV=production` the cookie is `Secure`.

## Rollback

- **Vercel:** dashboard → Deployments → previous good deployment → *Promote to Production*, or `vercel rollback`.
- **Containers:** set `IMAGE_TAG` to the previous tag and `docker compose -f docker-compose.prod.yml up -d`.
- **Database:** migrations are forward-only by default; take a Neon branch/backup before deploying a schema change and use `alembic downgrade -1` only for migrations written with a downgrade.

## Post-deploy checklist

- [ ] `/api/health/ready` returns `{"database":"ok"}`
- [ ] Register, sign out, sign in
- [ ] Upload a PDF and a DOCX; sections appear
- [ ] Run an analysis; the disclaimer is visible
- [ ] Delete the resume; its analysis disappears
- [ ] Password-reset email arrives (if Resend is configured)

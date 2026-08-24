# Deploying RootCause

## Architecture

- **Frontend** — Vercel (Next.js, `frontend/`)
- **Backend** — Render free web service (`backend/`, blueprint in `render.yaml`)
- **Demo determinism** — `demo_data/stage1_cache.json` and `demo_data/stage4_cache.json` are COMMITTED to git. Batch C's validated cards ship with the deploy and survive any restart on Render's ephemeral disk. Only brand-new batches would re-draw after a restart (runtime cache writes are not persistent on the free tier).

## One-time setup (account-bound steps)

1. **GitHub repo**: create an empty repo, then:
   ```powershell
   git remote add origin <YOUR_REPO_URL>
   git push -u origin main
   ```
2. **Render**: Dashboard → New + → Blueprint → select the repo. Render reads `render.yaml`. Set the `OPENROUTER_API_KEY` env var when prompted. Deploy.
3. **Vercel**: Add New → Project → import the same repo → set **Root Directory = `frontend`** (framework auto-detects Next.js). Before deploying, add env var:
   - `NEXT_PUBLIC_API_URL` = `https://<your-render-service>.onrender.com`
   Deploy.

## Post-deploy checklist (run after first deploys)

```powershell
$API = "https://<your-render-service>.onrender.com"
$WEB = "https://<your-vercel-app>.vercel.app"

# 1. health
Invoke-RestMethod "$API/health"

# 2. CORS preflight from the deployed frontend origin
Invoke-WebRequest -Uri "$API/api/diagnose" -Method Options -Headers @{Origin=$WEB; "Access-Control-Request-Method"="POST"}

# 3. insufficient-responses split
Invoke-RestMethod -Method Post -Uri "$API/api/diagnose" -ContentType "application/json" -Body '{"question":"q","responses":[{"response":"a"},{"response":"b"}]}'
# expect 422 with error=insufficient_responses

# 4. batch C cached paste (~3s, identical cards)
python backend\e2e_deploy_check.py $API
```

## Notes for demo day

- Render free services sleep after ~15 min idle; hit `/health` a minute before recording to warm it up (cold start ≈ 50 s).
- If you ever need fresh draws for a new batch, delete the relevant keys in `stage1_cache.json` / `stage4_cache.json`, commit, redeploy — then run once to re-lock.

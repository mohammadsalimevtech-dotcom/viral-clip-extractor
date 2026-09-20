# Viral Clip Extractor

YouTube video ka link do → AI (Claude) transcript padh kar sabse "viral-worthy" 30-40s moments
dhundta hai → ffmpeg unhe alag clips mein cut karta hai (captions ke saath).

**Pipeline:** `yt-dlp` (download) → `faster-whisper` (local transcription) → `Claude API`
(viral moment detection) → `ffmpeg` (cut + burn captions)

---

## 1. Local setup

```bash
# System dependency (video cutting ke liye zaroori)
# Mac:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# Python deps
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env banao
cp .env.example .env
# .env mein ANTHROPIC_API_KEY daalo (console.anthropic.com se milega)

# Server chalao
uvicorn app.main:app --reload --port 8000
```

Frontend test karne ke liye `frontend/index.html` ko browser mein direct kholo
(ya kisi bhi static file server se serve karo). Agar backend kisi doosre domain
pe deploy hai to `frontend/index.html` mein `API_BASE` variable update kar dena.

## 2. API kaise use karein

```bash
# Job submit karo
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=XXXXXXXX", "burn_captions": true}'
# Response: {"job_id": "..."}

# Status check karo (poll every 2-3s)
curl http://localhost:8000/jobs/<job_id>
# status: queued -> downloading -> transcribing -> analyzing -> cutting -> done
# "done" hone par response mein clips[] milega, har clip ka download_url

# Clip download karo
curl -O http://localhost:8000/clips/<clip_id>.mp4
```

## 3. Production deploy (backend)

Kaam karega kisi bhi jagah jo Docker support kare aur jahan long-running jobs
allowed hon (video processing CPU/RAM heavy hai):

**Render / Railway (sabse aasan):**
1. Is folder ko GitHub repo bana kar push karo.
2. Render/Railway pe "New Web Service" → repo connect karo → it auto-detects the `Dockerfile`.
3. Environment variable set karo: `ANTHROPIC_API_KEY`.
4. Deploy — aapko ek public URL milega (e.g. `https://your-app.onrender.com`).
5. `frontend/index.html` mein `API_BASE` ko is URL se update kar do.

**VPS (DigitalOcean / AWS EC2 / Hetzner):**
```bash
docker build -t viral-clip-extractor .
docker run -d -p 8000:8000 --env-file .env -v $(pwd)/storage:/app/storage viral-clip-extractor
```
Nginx/Caddy reverse proxy laga kar apna domain point kar do + HTTPS enable karo.

## 4. Frontend deploy

`frontend/index.html` ek static file hai — isse Vercel, Netlify, GitHub Pages,
ya `python -m http.server` se kahin bhi serve kar sakte ho. Bas `API_BASE`
apne deployed backend URL pe point kar dena.

## 5. Important notes

- **Cost:** Whisper transcription local/free chalta hai (CPU pe). Sirf Claude
  API calls (transcript analysis ke liye, chhota text) ka cost lagega —
  per-video paisa 1 rupee se bhi kam hota hai typically.
- **Speed:** Lambi videos (1hr+) pe transcription CPU pe slow ho sakti hai.
  Zyada traffic ke liye GPU instance ya `WHISPER_MODEL_SIZE=tiny` use karo.
- **Scaling:** Abhi jobs in-memory dict + background thread mein chal rahe
  hain — ek server ke liye theek hai. Zyada traffic ke liye Redis + Celery/RQ
  queue mein migrate karna.
- **Legal:** YouTube videos download karna unke Terms of Service ke against
  ja sakta hai agar aap doosron ka copyrighted content bina permission ke
  reuse/republish karte ho. Ye tool sirf apni videos, licensed content, ya
  creator ki permission wale content pe use karo — production launch se
  pehle ek baar legal opinion le lena.

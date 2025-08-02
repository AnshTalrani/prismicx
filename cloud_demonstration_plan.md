# Cloud Demonstration Plan

> **Goal**: show recruiters a live, cloud-hosted demo that proves you can design, containerise and deploy multi-LLM micro-services using FastAPI, LangChain, Docker, event-driven orchestration and managed databases.

---

## 1. Flows to Showcase

### 1.1 Chat-Bot Flow
```
communication-base → LLM & RAG stack → MongoDB (conversation history)
```
* Public endpoint: `POST /api/chat` (shown in Swagger UI)
* Highlights: FastAPI async workers, LangChain RAG chain, structured logging, Docker, MongoDB Atlas.

### 1.2 Outreach Flow
```
management-systems → agent → outreach bots (sales + expert) → CRM updates
```
* Campaigns & contacts live in the CRM schema (Postgres).
* **Sales bot** selects decisions using **campaign templates** (JSON) → extracts info, moves stages, schedules follow-ups.
* **Expert bots** supply industry-specific knowledge via the agent bridge.
* Demonstrates: template-driven orchestration, multi-bot coordination, event bus, Redis streams, FastAPI.

---

## 2. Cloud Architecture Diagram
```
┌───────────────────────┐      ┌──────────────────────────┐
│  Front-end (Swagger)  │────►│  communication-base (api) │
└───────────────────────┘      │   Docker / Python / LLM   │
                               └──────────▲───────────────┘
                                          │REST / JSON
                               ┌──────────┴───────────────┐   Streams  ┌──────────────┐
                               │      agent microservice  │───────────►│  expert bots │
                               │  Docker / FastAPI / RQ   │            └──────────────┘
                               └──────────▲───────────────┘
                                          │REST
┌────────────┐   Webhook   ┌──────────────┴───────────────┐
│  CRM DB    │◄───────────│  management-systems service   │
│ Postgres   │            │   Docker / FastAPI           │
└────────────┘            └───────────────────────────────┘

MongoDB Atlas stores chat history; Redis (optional) backs queues.
```

---

## 3. Cloud Resources
| Component | Service | Plan |
|-----------|---------|------|
| communication-base | Render / Cloud Run container | Starter (512 MB) |
| agent | Render / Cloud Run | Starter |
| management-systems | Render / Cloud Run | Starter |
| MongoDB Atlas | Shared M0 | Free |
| Postgres (Supabase / Railway) | Hobby | $0-5 |
| Redis (Upstash) | Free tier | Free |

---

## 4. Containerisation Steps
1. **Dockerfile** in each microservice:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. Multi-service `docker-compose.yml` for local testing.
3. Build & push images: `docker build -t ghcr.io/<user>/<svc>:v1 .`.

---

## 5. Deployment Pipeline
| Stage | Tool |
|-------|------|
| Build  | GitHub Actions (`docker buildx`) |
| Push   | GHCR / GCR |
| Deploy | Render Blueprint or Cloud Run service YAML |
| Migrate| Alembic job for Postgres schema |

---

## 6. Live Demo Script
1. Open Swagger for **communication-base** → send chat message, show LLM response & MongoDB document.
2. In **management-systems** Swagger, `POST /api/campaigns` with sample payload.
3. Watch **agent** logs – campaign template loaded, sales bot requests expert bot.
4. Show CRM record updated (stage → interest) in Postgres.
5. (Optional) Show Grafana dashboard with message counters.

---

## 7. Talking Points
* Microservice architecture – independent deploys, clear domains.
* LLM integration via LangChain & custom RAG chain.
* Event-driven orchestration (Redis streams & internal async tasks).
* Infrastructure-as-code in Render Blueprint / `cloudrun.yaml`.
* Security: JWT auth, OAuth2 scheme in management-systems.
* Observability: Prometheus metrics + structured logs.

---

## 8. Next Actions
- [ ] Finish three TODOs in `consultancy_bot_handler.py`
- [x] Replace placeholder `user_id` extraction in management-systems routes
- [ ] Add `/healthz` to all FastAPI apps
- [ ] Write GitHub Actions workflow to build & deploy
- [ ] Record 3-minute screencast following demo script

---

> **Result**: Recruiters see live endpoints, Swagger docs, and a clearly articulated cloud deployment showcasing Docker, databases, APIs, UIs, LangChain, RAG, and multi-bot orchestration.

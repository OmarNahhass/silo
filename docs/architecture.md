# System Architecture

```mermaid
flowchart LR
    subgraph Client
        Browser["React SPA<br/>(Vite + TypeScript)"]
    end

    subgraph "Cloudflare Pages"
        Pages["Static frontend hosting"]
    end

    subgraph "Fly.io"
        API["FastAPI backend<br/>(api.py)"]
        DB[("SQLite<br/>predictions.db")]
    end

    subgraph External
        YF["Yahoo Finance<br/>(yfinance)"]
    end

    Browser -->|HTTPS| Pages
    Pages -->|serves static assets| Browser
    Browser -->|"REST /api/*"| API
    API -->|fetch price history & analyst data| YF
    API -->|read / write predictions| DB
```

- **Frontend**: React 19 + TypeScript, built with Vite, deployed to Cloudflare Pages.
- **Backend**: FastAPI, deployed to Fly.io (scales to zero when idle).
- **Persistence**: a single SQLite file on a Fly.io volume, tracking every prediction the app has
  ever made so accuracy can be measured after the fact (see [Track Record](track-record-sequence.md)).
- **Deploys**: both sides auto-deploy on push to `main` via GitHub Actions
  (`.github/workflows/deploy.yml`).

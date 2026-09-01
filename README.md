# The Challenge 🏆

> [!WARNING]  
> Entirely vibecoded. Use at your own risk. This was a quick and dirty challenge tracking app.

> [!NOTE]
> A frontend distribution has been provided in `frontend/dist`. Ideally you should build it yourself, but this makes it easier to get up and running without having to touch node.js at all.

# LLMSpiel:

A group challenge tracker: the master user (**vas**) defines the challenges and starts
the clock, everyone signs up and logs contributions (with optional photo proof), and a
leaderboard plus a per-person progress grid show how the group is doing.

## Run it

The backend (FastAPI + SQLite) also serves the built frontend from `frontend/dist`,
so deployment only needs Python:

```sh
cd backend
python3 -m venv .venv          # first time only
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. Friends on the same network can use `http://<your-ip>:8000`.

For frontend development, run the Vite dev server (port 5173, proxies `/api` to the
backend) and rebuild `dist/` before deploying:

```sh
cd frontend
npm install                    # first time only
npm run dev -- --host          # develop at http://localhost:5173
npm run build                  # refresh dist/ for deployment
```

## How it works

- Sign up with the username **vas** to become the master user. Everyone else who signs
  up automatically joins the challenge.
- The master creates challenges in the Admin tab. Each has an amount and a unit, and is
  either **per person** (target = amount × number of participants, e.g. 10 bananas per
  person) or a **fixed total** (e.g. 1 minecraft finish).
- The master hits **Start** — the stopwatch begins and contributions open. **Stop**
  freezes the clock and closes contributions; **Reset** wipes the timer and all
  contributions.
- Anyone can log a contribution to any challenge, with an optional photo as proof.
  You can delete your own contributions; the master can delete anyone's.
- **Leaderboard** points = the percentage of each challenge's target you contributed,
  summed across all challenges (so a 1-off fixed challenge is worth as much as a big
  per-person one).
- **Progress** shows the full person × challenge grid.

Data lives in `backend/challenge.db` (SQLite); photos in `backend/uploads/`.

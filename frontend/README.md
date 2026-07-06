# AI Video Assistance — Frontend

React + Vite + Tailwind + daisyUI frontend for the AI Video Assistance pipeline
(transcribe → summarize → extract action items/decisions/questions → chat via RAG).

## Setup

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api/*` requests to
`http://localhost:8000` (your Flask backend — see `vite.config.js`).

## Build for production

```bash
npm run build
```

Outputs static files to `dist/`. Set `VITE_API_URL` (e.g. in a `.env` file) to
point at your deployed backend if it's not served from the same origin/proxy:

```
VITE_API_URL=https://your-backend.example.com/api
```

## Structure

```
src/
  App.jsx                 # layout: Sidebar + ResultsPanel + ChatContainer
  components/
    Sidebar.jsx            # source input (URL / file upload) + translate toggle
    ResultsPanel.jsx        # title, summary, action items, decisions, questions, transcript tabs
    ChatContainer.jsx       # RAG chat UI (styled after the original chat component)
    MessageInput.jsx
    Skeleton/
      ResultsSkeleton.jsx
      MessagesSkeleton.jsx
  store/
    useAppStore.js          # zustand store: process video + chat state
  lib/
    axios.js
```

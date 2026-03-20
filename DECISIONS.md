# Architectural Decisions

- **Backend Framework**: `FastAPI` with `asyncpg` was chosen for high concurrency, auto-generated OpenAPI docs, and type safety constraints via Pydantic matching our database schemas tightly.
- **Dependency Management**: Standard `pip` with `requirements.txt` for simplicity, stability, and broad CI/CD support.
- **Frontend Stack**: `React 18`, `Vite`, `TailwindCSS` with `lucide-react` icons. Ensures fast compilation and a responsive, dynamic UI out of the box.
- **State Management**: `Zustand` was selected over Redux to reduce boilerplate for auth persistence (`useAuthStore`). Backend fetches were simplified to standard hooks with `axios` instances.
- **AI Service**: `Google Gemini` (`gemini-2.5-flash`) provides voice and receipt parsing capabilities via the `google-genai` SDK on the backend. Fallback prompt-based intelligence ensures robust JSON returning.
- **Database**: PostgreSQL standard image running on port 5433 using `SQLAlchemy 2.0` declarative patterns. `Alembic` manages schema migrations.
- **Mobile**: `Capacitor`. Wraps our fast Vite SPA into an Android/iOS shell effortlessly while keeping a single codebase.
- **Auth**: JWT based stateless session management with access and refresh tokens. Fallback routes handle `401` gracefully by attempting refresh through front-end Axios interceptors.

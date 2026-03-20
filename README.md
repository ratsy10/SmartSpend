# SmartSpend

**Voice-first AI-powered personal expense tracker**

SmartSpend is an intelligent finance tracker. Its goal is to allow lightning fast logging of everyday transactions using powerful backend LLM parsers coupled with a snappy, mobile-first UI.

## Features
- **Voice logging**: Describe your expense (e.g. "I paid 15 dollars for lunch at Subway") and watch it categorize and assign the amount instantly.
- **Receipt Scan**: Snap and upload pictures of receipts for automatic categorization.
- **Smart Insights**: Receive automated tips on budget tracking.
- **Full View**: Track categorized spending across months, complete with data visualizations.
- **PWA and Native**: Works flawlessly on the web, and deploys to iOS/Android via Capacitor.

## Architecture
- **API**: FastAPI (Python)
- **DB**: PostgreSQL (SQLAlchemy + asyncpg) + Redis
- **UI**: React 18 + Vite + Tailwind CSS + Zustand
- **AI**: Google Gemini (GenAI SDK)

Check out `SETUP.md` to run the stack, and `DECISIONS.md` to see why the engine was built this way.

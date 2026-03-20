# Setup & Deployment

## Prerequisites
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose
- API Keys: 
  - `GEMINI_API_KEY` (For Gemini AI capabilities)

## Running Locally

### 1. Database & Services
Run the PostgreSQL and Redis containers. Note that Postgres runs on port 5433 to avoid local conflicts. *(Important: Make sure Docker Desktop is open and running first!)*
```bash
docker-compose up -d
```

### 2. Backend
Navigate to the `backend` directory, install dependencies, run migrations, and start the server:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
The API will be available at http://localhost:8000
Interactive docs at http://localhost:8000/docs

### 3. Frontend
Install npm packages and start Vite:
```bash
cd frontend
npm install
npm run dev
```
The frontend will be at http://localhost:5173

## 📱 Mobile Deployment (Android)

To run the Android app, you will need to install Android Studio. Since this project uses Capacitor to wrap the web app into a native Android application, the final build and deployment happen inside Android Studio.

### 1. Install Android Studio
1. Download [Android Studio](https://developer.android.com/studio) and install it on your computer.
2. Open Android Studio and complete the initial setup wizard. This process will automatically download the required Android SDKs and platform tools.

### 2. Prepare the Capacitor Build
Run the following command in the `frontend` directory:
```bash
cd frontend
npm run build:android
```
This compiles your Vite project into native assets and synchronizes them to the Capacitor `android` folder. 
*(Note: If Android Studio fails to open automatically at the end of this script, proceed to step 3).*

### 3. Open & Run Deploy
1. Open Android Studio manually.
2. Click **Open** (or *Open an existing project*).
3. Select the `c:\Storage\Projects\SmartSpend\frontend\android` folder.
4. Wait for Android Studio to finish its initial "Gradle Sync" (this usually takes a minute and shows a progress bar at the bottom).
5. **To test on a real device:** Connect your Android phone via USB and ensure **USB Debugging** is enabled in Developer Options.
6. **To test on an emulator:** Open the Device Manager in Android Studio and create/start a Virtual Device.
7. Finally, select your device in the top toolbar and click the green ▶️ **Run 'app'** button to install and launch SmartSpend!

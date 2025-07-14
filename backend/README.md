# AgentOrchestra Backend

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables (see `.env.example`).
4. Run the app:
   ```bash
   python wsgi.py
   ```

## Environment Variables
- `SECRET_KEY`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## Deployment
- Use Gunicorn or deploy as a Vercel serverless function. 
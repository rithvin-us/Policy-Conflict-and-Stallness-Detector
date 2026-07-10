# Policy Guardian AI — backend image.
# NOTE: build with the repository ROOT as context so both `backend/` and
# `sample_data/` are available, e.g.:
#   docker build -f backend/Dockerfile -t policy-guardian-api .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for layer caching.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source + the sample corpus used for first-boot seeding.
COPY backend/app ./app
COPY backend/pytest.ini .
COPY sample_data /sample_data

ENV SEED_POLICY_DIR=/sample_data/policies \
    DATABASE_URL=sqlite:////app/policyguardian.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/health').status_code==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

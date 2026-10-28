FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

# model artifacts (backend/app/artifacts/) are committed to the repo
# and copied in above — no separate volume needed to run the service,
# only to swap in a newly retrained model without a rebuild

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

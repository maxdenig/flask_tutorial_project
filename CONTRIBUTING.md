# CONTRIBUTING

## How to Run Locally

Run in cmd:
```
docker run -dp 5001:5000 -w /app -v "/c/repo/flask_api:/app" flask-proj-jwt-migr
```

Dockerfile:
```
FROM python:3.11
EXPOSE 5000
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host", "0.0.0.0"]
```

# ==========================================
# Stage 1: Build Frontend (Node.js)
# ==========================================
FROM node:18-slim as frontend_builder

WORKDIR /app/frontend

# Copy frontend dependency files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Build the React application
RUN npm run build


# ==========================================
# Stage 2: Run Backend (Python)
# ==========================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/


# Copy built frontend assets from Stage 1
# Note: app.py expects static_folder='../../frontend/dist' relative to backend/app/main.py
# So we place it in /app/frontend/dist to match that relative path logic
COPY --from=frontend_builder /app/frontend/dist ./frontend/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 backend.app.main:app

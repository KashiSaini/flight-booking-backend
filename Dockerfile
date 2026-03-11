# 1. Use the official lightweight Python image
FROM python:3.11-slim

# 2. Tell Docker to work out of a folder called /code inside the container
WORKDIR /code

# 3. Copy only the requirements file first (this makes future builds faster)
COPY requirements.txt .

# 4. Install all the libraries from your requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project files into the container
COPY . .

# 6. Expose the port FastAPI runs on
# EXPOSE 8000

# # 7. The command to start your app
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Expose port
EXPOSE 8080

# Start command
# CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
CMD ["bash", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
# Use official Python image as a base image
FROM python:3.11-slim

# Install necessary dependencies (including gcc)
RUN apt-get update && \
    apt-get install -y libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies from the requirements.txt for fastapi_als_wrapper
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8001

# Define environment variables for database connection
# You can use environment variables from Docker Compose here
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_NAME=course_recommendation
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

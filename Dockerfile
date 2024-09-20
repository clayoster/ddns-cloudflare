# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8080

# Allow stdout from python app through to docker logs
ENV PYTHONUNBUFFERED 1

# Run the python app with gunicorn and bind to port 8080
CMD ["gunicorn", "-w", "1", "--error-logfile", "-", "--log-level", "debug", "-b", "0.0.0.0:8080", "app:app"]
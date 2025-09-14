################
## Base Stage ##
################
# Use an official Python runtime as the base image
FROM python:3.13-alpine AS base

# Allow stdout from python app through to docker logs
ENV PYTHONUNBUFFERED=1

# Define the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install available updates, python packages from requirements.txt
# and create app user
RUN set -ex \
    && apk upgrade --available --no-cache \
    && apk add curl --no-cache \
    && rm -rf /var/cache/apk/* \
    && pip install --no-cache-dir -r app-requirements.txt \
    && pip cache purge \
    && adduser -D app

# Expose port 8080
EXPOSE 8080

###############
## Dev Stage ##
###############
FROM base AS dev

# Install development tools
RUN set -ex \
    && apk add git \
    && rm -rf /var/cache/apk/* \
    && pip install --no-cache-dir -r app-dev-requirements.txt \
    && pip cache purge

# Add environment variables
ENV PYTHONDONTWRITEBYTECODE=1

################
## Prod Stage ##
################
FROM base AS prod

# Run app as 'app' user
USER app

# Run the python app with gunicorn (settings are in gunicorn.conf.py)
CMD ["gunicorn", "app:app"]

# Application halthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

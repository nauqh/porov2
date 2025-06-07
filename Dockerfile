FROM python:3.12-slim-bookworm

# Copy uv from the specified image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv sync --locked

# Run the bot
CMD ["uv", "run", "-m", "bot.py"]

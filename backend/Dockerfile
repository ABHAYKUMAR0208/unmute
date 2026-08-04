FROM python:3.11-slim

WORKDIR /app

# build-essential + curl kept in case sphn needs to build from source on
# this platform (no prebuilt wheel available). Rust toolchain is added
# only if the plain pip install fails; see requirements.txt comment.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Try the normal install first; if sphn has no prebuilt wheel for this
# platform, fall back to installing Rust and retrying.
RUN pip install --no-cache-dir -r requirements.txt || \
    (curl https://sh.rustup.rs -sSf | sh -s -- -y && \
     . "$HOME/.cargo/env" && \
     pip install --no-cache-dir -r requirements.txt)

COPY app ./app

RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8000

# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#     CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

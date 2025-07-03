# STAGE 1: THE FORGE - USING THE FULL, UNBROKEN BASE IMAGE
FROM rust:1 as builder

# INSTALL THE ENTIRE WAR CHEST.
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 \
    build-essential \
    pkg-config \
    libtesseract-dev \
    libleptonica-dev \
    libopencv-dev \
    clang

# NO MORE PATH HACKS. THE FULL IMAGE SHOULD KNOW WHAT IT'S DOING.
WORKDIR /usr/src/app

COPY Cargo.toml ./
COPY src ./src
# BUILD.
RUN cargo build --release

# STAGE 2: THE DEPLOYED WEAPON
FROM debian:bullseye-slim

# INSTALL RUNTIME NEEDS
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 \
    tesseract-ocr \
    wamerican \
    libopencv-core4.5 \
    libopencv-imgproc4.5 \
    libopencv-imgcodecs4.5 \
    && rm -rf /var/lib/apt/lists/*

# COPY THE COMPILED BRAIN FROM THE FORGE
COPY --from=builder /usr/src/app/target/release/brain /usr/local/bin/brain

# EXECUTE
CMD ["brain"]

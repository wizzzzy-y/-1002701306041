# STAGE 1: THE FORGE - OMEGA CONFIG
FROM rust:1-slim as builder

# INSTALL THE ENTIRE DAMN ARSENAL. NO MORE GAMES.
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 \
    build-essential \
    pkg-config \
    libtesseract-dev \
    libleptonica-dev \
    libopencv-dev \
    clang \
    libclang-dev

# TAKE THE BUILDER BY THE HAND AND SHOW IT WHERE THE LIBRARY IS
ENV LIBCLANG_PATH=/usr/lib/llvm-11/lib

WORKDIR /usr/src/app

COPY Cargo.toml ./
COPY src ./src
# BUILD THE WEAPON. FINAL ATTEMPT.
RUN cargo build --release

# STAGE 2: THE DEPLOYED KILLER
FROM debian:bullseye-slim

# INSTALL RUNTIME NEEDS
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 \
    tesseract-ocr \
    wamerican \
    libopencv-core4.5 \
    libopencv-imgproc4.5 \
    libopencv-imgcodecs4.5 \
    && rm -rf /var/lib/apt/lists/*

# COPY THE FINISHED BRAIN
COPY --from=builder /usr/src/app/target/release/brain /usr/local/bin/brain

# EXECUTE
CMD ["brain"]

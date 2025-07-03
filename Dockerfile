# STAGE 1: THE FORGE - PROFESSIONAL GRADE
FROM rust:1-slim as builder

# INSTALL THE ENTIRE C++ WAR CHEST
# WE ADD 'libclang-dev' - THIS IS THE KILL SHOT
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 \
    build-essential \
    pkg-config \
    libtesseract-dev \
    libleptonica-dev \
    libopencv-dev \
    clang \
    libclang-dev

WORKDIR /usr/src/app

COPY Cargo.toml ./
# NO MORE DUMMY BUILDS. BUILD DEPS WITH THE REAL SOURCE.
COPY src ./src
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

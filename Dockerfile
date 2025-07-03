# STAGE 1: THE FORGE (COMPILER)
FROM rust:1-slim as builder

# INSTALL C++ DEPENDENCIES WITH RETRY LOGIC
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 build-essential pkg-config libtesseract-dev libleptonica-dev libopencv-dev clang

WORKDIR /usr/src/app

COPY Cargo.toml ./
# Build ONLY the dependencies
RUN mkdir src/ && echo "fn main() {}" > src/main.rs && cargo build --release

COPY src ./src
# Build the final binary
RUN cargo build --release

# STAGE 2: THE WAR MACHINE (RUNTIME)
FROM debian:bullseye-slim

# INSTALL RUNTIME DEPENDENCIES WITH RETRY LOGIC
RUN apt-get update && apt-get install -y -o Acquire::Retries=3 tesseract-ocr wamerican libopencv-core4.5 libopencv-imgproc4.5 libopencv-imgcodecs4.5 && rm -rf /var/lib/apt/lists/*

# Copy the binary from the forge
COPY --from=builder /usr/src/app/target/release/brain /usr/local/bin/brain

# RUN
CMD ["brain"]

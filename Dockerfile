# STAGE 1: THE FORGE (COMPILER)
# We use the official Rust image to build our killer binary
FROM rust:1-slim as builder

# Install the C++ dependencies that OpenCV and Tesseract need to link against
RUN apt-get update && apt-get install -y build-essential pkg-config libtesseract-dev libleptonica-dev libopencv-dev clang

WORKDIR /usr/src/app

# Copy the dependency list first to cache the layer
COPY Cargo.toml ./
# Build ONLY the dependencies. This will be fast on future builds if only code changes.
RUN mkdir src/ && echo "fn main() {}" > src/main.rs && cargo build --release

# Now copy the rest of the code
COPY src ./src
# Build the final, optimized binary
RUN cargo build --release

# STAGE 2: THE WAR MACHINE (RUNTIME)
# Start from a tiny, clean image for deployment
FROM debian:bullseye-slim

# Install ONLY the running dependencies, not the whole compiler
RUN apt-get update && apt-get install -y tesseract-ocr wamerican libopencv-core4.5 libopencv-imgproc4.5 libopencv-imgcodecs4.5 && rm -rf /var/lib/apt/lists/*

# Copy the killer binary from the forge
COPY --from=builder /usr/src/app/target/release/brain /usr/local/bin/brain

# RUN THE MACHINE
CMD ["brain"]

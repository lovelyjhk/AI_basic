# Multi-stage build for MedGuard

# Stage 1: Build Rust backend
FROM rust:1.75-slim as rust-builder

WORKDIR /app
COPY backend/Cargo.toml backend/Cargo.lock ./backend/
COPY backend/src ./backend/src/
COPY config.toml ./

RUN cd backend && cargo build --release

# Stage 2: Build React frontend
FROM node:18-slim as node-builder

WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Stage 3: Runtime
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy built artifacts
COPY --from=rust-builder /app/backend/target/release/medguard /app/
COPY --from=node-builder /app/frontend/build /app/frontend/build
COPY config.toml /app/

# Create directories
RUN mkdir -p /app/test_medical_data /app/backups

# Expose ports
EXPOSE 8080 3000

# Start the application
CMD ["/app/medguard"]

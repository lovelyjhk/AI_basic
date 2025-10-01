#!/bin/bash

echo "🏥 MedGuard - Starting Medical Ransomware Defense System"
echo "=================================================="
echo ""

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install from https://rustup.rs/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install from https://nodejs.org/"
    exit 1
fi

echo "✓ Rust version: $(rustc --version)"
echo "✓ Node version: $(node --version)"
echo ""

# Build backend
echo "🔨 Building Rust backend..."
cd backend
cargo build --release
if [ $? -ne 0 ]; then
    echo "❌ Backend build failed"
    exit 1
fi
echo "✓ Backend built successfully"
echo ""

# Generate test data
echo "📁 Generating test medical data..."
cargo run --release --bin generate_test_data
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
echo "✓ Frontend dependencies installed"
echo ""

# Start backend in background
echo "🚀 Starting backend server..."
cd ../backend
cargo run --release > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend running (PID: $BACKEND_PID)"
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3
echo ""

# Start frontend
echo "🎨 Starting frontend dashboard..."
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "✓ Frontend running (PID: $FRONTEND_PID)"
echo ""

echo "=================================================="
echo "✅ MedGuard is now running!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8080/api/status"
echo ""
echo "📝 Test the system:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Run attack simulation: cd backend && cargo run --bin simulate_attack"
echo "   3. Watch the dashboard detect and prevent the attack!"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo "=================================================="

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '🛑 MedGuard stopped'; exit 0" INT

wait

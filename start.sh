#!/bin/bash
# ClipAI Startup Script

echo "================================"
echo "ClipAI Startup Script"
echo "================================"
echo ""

# Check if backend is running
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo "Starting Backend Server..."
cd backend
# Start backend in background
python main.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if curl -s "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    echo "✓ Backend is running at $BACKEND_URL"
else
    echo "✗ Backend failed to start"
    echo "  Check backend logs for errors"
fi

echo ""
echo "Starting Frontend Server..."
cd ../frontend

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "================================"
echo "ClipAI is ready!"
echo "================================"
echo "Frontend: $FRONTEND_URL"
echo "Backend API: $BACKEND_URL"
echo "API Docs: $BACKEND_URL/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

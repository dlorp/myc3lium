#!/usr/bin/env bash
set -euo pipefail

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🍄 Starting MYC3LIUM Development Servers${NC}"
echo "=========================================="

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo -e "${GREEN}✨ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "\n${BLUE}Starting backend (FastAPI)...${NC}"
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
deactivate
cd ..
echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"

# Give backend a moment to start
sleep 2

# Start frontend
echo -e "\n${BLUE}Starting frontend (Vite + React)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"

echo -e "\n${GREEN}=========================================="
echo -e "✨ Development servers running!"
echo -e "==========================================${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop all servers"

# Wait for background processes
wait

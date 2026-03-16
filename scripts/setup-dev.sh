#!/usr/bin/env bash
set -euo pipefail

echo "🍄 MYC3LIUM Development Environment Setup"
echo "=========================================="

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 20+${NC}"
    exit 1
fi
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js version must be 18 or higher (found: $(node -v))${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node -v)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm $(npm -v)${NC}"

# Setup frontend
echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "node_modules exists, skipping npm install (run 'npm ci' to reinstall)"
fi
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Setup backend
echo -e "\n${YELLOW}Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
deactivate
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..

# Create .env files if they don't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env from .env.example${NC}"
    else
        echo -e "${YELLOW}⚠ No .env.example found, skipping .env creation${NC}"
    fi
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo -e "✨ Setup complete!"
echo -e "==========================================${NC}"
echo -e "\nNext steps:"
echo -e "  1. Review and update .env configuration"
echo -e "  2. Run: ${YELLOW}./scripts/run-dev.sh${NC} to start dev servers"
echo -e "  3. Frontend: http://localhost:3000"
echo -e "  4. Backend: http://localhost:8000"

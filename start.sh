#!/bin/bash
# Quick Start Script for Trading Signal Terminal

set -e  # Exit on error

echo "🚀 Trading Signal Terminal - Local Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

echo -e "${BLUE}✓ Python & Node.js found${NC}\n"

# Setup Python environment
echo -e "${BLUE}[1/5] Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate || . venv/Scripts/activate
pip install -q --upgrade pip

echo -e "${BLUE}[2/5] Installing Python dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r functions/signal_function/requirements.txt

# Setup Playwright
echo -e "${BLUE}[3/5] Installing Playwright browser...${NC}"
python -m playwright install -q chromium

# Setup Frontend
echo -e "${BLUE}[4/5] Installing frontend dependencies...${NC}"
cd dashboard
npm install -q
cd ..

# Setup environment
echo -e "${BLUE}[5/5] Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo -e "${YELLOW}📝 Edit .env with your Quotex credentials before running!${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}\n"
echo "📍 Quick Start Commands:"
echo "   • Frontend:  cd dashboard && npm run dev"
echo "   • Backend:   cd functions/signal_function && python -m flask run"
echo "   • Git Push:  git add . && git commit -m 'message' && git push"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 API:      http://localhost:5000/api/signal"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

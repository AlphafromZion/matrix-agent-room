#!/usr/bin/env bash
# matrix-agent-room: First-time setup helper
# Run this once to configure your environment.

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   matrix-agent-room — Setup                  ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# --- Check prerequisites ---
echo -e "${CYAN}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Install it: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✓ Docker Compose (plugin) found${NC}"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}✓ docker-compose found${NC}"
else
    echo -e "${RED}✗ Docker Compose not found. Install it: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

echo ""

# --- Create .env from example ---
if [ -f .env ]; then
    echo -e "${YELLOW}⚠ .env already exists. Skipping copy (delete it to regenerate).${NC}"
else
    echo -e "${CYAN}Creating .env from .env.example...${NC}"
    cp .env.example .env

    # Generate secrets
    echo -e "${CYAN}Generating secrets...${NC}"

    REGISTRATION_SECRET=$(openssl rand -hex 32)
    MACAROON_SECRET=$(openssl rand -hex 32)
    FORM_SECRET=$(openssl rand -hex 32)
    POSTGRES_PASS=$(openssl rand -hex 16)

    # Replace placeholders in .env
    sed -i "s/SYNAPSE_REGISTRATION_SHARED_SECRET=CHANGE_ME_GENERATE_WITH_OPENSSL/SYNAPSE_REGISTRATION_SHARED_SECRET=${REGISTRATION_SECRET}/" .env
    sed -i "s/SYNAPSE_MACAROON_SECRET_KEY=CHANGE_ME_GENERATE_WITH_OPENSSL/SYNAPSE_MACAROON_SECRET_KEY=${MACAROON_SECRET}/" .env
    sed -i "s/SYNAPSE_FORM_SECRET=CHANGE_ME_GENERATE_WITH_OPENSSL/SYNAPSE_FORM_SECRET=${FORM_SECRET}/" .env
    sed -i "s/POSTGRES_PASSWORD=CHANGE_ME_USE_A_STRONG_PASSWORD/POSTGRES_PASSWORD=${POSTGRES_PASS}/" .env

    echo -e "${GREEN}✓ .env created with generated secrets${NC}"
fi

echo ""

# --- Create bot config from example ---
if [ -f bots/config.yaml ]; then
    echo -e "${YELLOW}⚠ bots/config.yaml already exists. Skipping copy.${NC}"
else
    echo -e "${CYAN}Creating bots/config.yaml from example...${NC}"
    cp bots/config.yaml.example bots/config.yaml
    echo -e "${GREEN}✓ bots/config.yaml created — edit it with your model settings${NC}"
fi

echo ""

# --- Summary ---
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Setup Complete — Next Steps                ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "1. Edit .env with your domain:"
echo "   nano .env"
echo ""
echo "2. Edit bots/config.yaml with your models:"
echo "   nano bots/config.yaml"
echo ""
echo "3. Start the stack:"
echo "   ${COMPOSE_CMD} up -d"
echo ""
echo "4. Create bot accounts:"
echo "   bash scripts/create-bot-accounts.sh"
echo ""
echo "5. Open Element Web:"
echo "   http://localhost:8080"
echo ""
echo -e "${GREEN}Happy chatting! 🤖${NC}"

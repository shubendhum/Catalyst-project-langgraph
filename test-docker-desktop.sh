#!/bin/bash
# Catalyst Enterprise Migration - Docker Desktop Testing Script
# Run this on your local machine with Docker Desktop

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Catalyst Enterprise Migration - Testing Script                ║"
echo "║  Phases 1-4: Infrastructure, Agents, Git, Preview              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
TOTAL=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✅ PASS${NC} - $1"
    ((PASSED++))
    ((TOTAL++))
}

fail_test() {
    echo -e "${RED}❌ FAIL${NC} - $1"
    echo -e "   ${RED}Error: $2${NC}"
    ((FAILED++))
    ((TOTAL++))
}

section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

info() {
    echo -e "${YELLOW}ℹ  $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# ============================================
# PRE-FLIGHT CHECKS
# ============================================

section "Pre-Flight Checks"

info "Checking Docker Desktop..."
if ! docker info > /dev/null 2>&1; then
    fail_test "Docker Desktop" "Docker is not running. Please start Docker Desktop."
    exit 1
else
    pass_test "Docker Desktop is running"
fi

info "Checking docker-compose..."
if ! docker-compose --version > /dev/null 2>&1; then
    fail_test "docker-compose" "docker-compose not found"
    exit 1
else
    pass_test "docker-compose is available"
fi

info "Checking make..."
if ! make --version > /dev/null 2>&1; then
    fail_test "make" "make not found"
    exit 1
else
    pass_test "make is available"
fi

# ============================================
# STEP 1: CLEANUP & FRESH START
# ============================================

section "Step 1: Cleanup & Fresh Start"

info "Stopping existing services..."
make stop-artifactory 2>/dev/null || true
success "Services stopped"

info "Cleaning up old volumes..."
read -p "This will DELETE all data. Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    make fix-all-volumes || true
    success "Volumes cleaned"
else
    echo "Skipping cleanup. Using existing data."
fi

# ============================================
# STEP 2: START SERVICES
# ============================================

section "Step 2: Starting Complete Stack (9 Services)"

info "This will start:"
echo "  1. Postgres (state DB)"
echo "  2. MongoDB (conversations)"
echo "  3. Redis (caching)"
echo "  4. Qdrant (vector DB)"
echo "  5. RabbitMQ (event streaming)"
echo "  6. Traefik (routing)"
echo "  7. Backend (API + agents)"
echo "  8. Frontend (UI)"
echo ""

info "Starting services..."
make start-artifactory

info "Waiting for services to initialize (30 seconds)..."
sleep 30

# ============================================
# STEP 3: VERIFY SERVICES
# ============================================

section "Step 3: Verify All Services Running"

info "Checking service status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep catalyst

info "Counting running services..."
SERVICE_COUNT=$(docker ps --filter "name=catalyst" --format "{{.Names}}" | wc -l)

if [ "$SERVICE_COUNT" -ge 8 ]; then
    pass_test "Service Count" "$SERVICE_COUNT services running"
else
    fail_test "Service Count" "Expected 8+, got $SERVICE_COUNT"
fi

# Check specific services
info "Verifying critical services..."

for service in postgres mongodb redis rabbitmq backend frontend; do
    if docker ps | grep -q "catalyst-${service}"; then
        pass_test "Service: catalyst-${service}"
    else
        fail_test "Service: catalyst-${service}" "Container not running"
    fi
done

# ============================================
# STEP 4: ENVIRONMENT DETECTION
# ============================================

section "Step 4: Environment Detection Test"

info "Testing environment detection API..."
ENV_RESPONSE=$(curl -s http://localhost:8001/api/environment/info)

if echo "$ENV_RESPONSE" | jq -e '.environment == "docker_desktop"' > /dev/null; then
    pass_test "Environment Detection" "Correctly detected docker_desktop"
else
    fail_test "Environment Detection" "Expected docker_desktop, got: $(echo $ENV_RESPONSE | jq -r .environment)"
fi

if echo "$ENV_RESPONSE" | jq -e '.orchestration_mode == "event_driven"' > /dev/null; then
    pass_test "Orchestration Mode" "Event-driven mode enabled"
else
    fail_test "Orchestration Mode" "Expected event_driven"
fi

if echo "$ENV_RESPONSE" | jq -e '.features.postgres == true' > /dev/null; then
    pass_test "Postgres Feature" "Enabled"
else
    fail_test "Postgres Feature" "Should be enabled in Docker Desktop"
fi

if echo "$ENV_RESPONSE" | jq -e '.features.event_streaming == true' > /dev/null; then
    pass_test "Event Streaming" "Enabled"
else
    fail_test "Event Streaming" "Should be enabled"
fi

if echo "$ENV_RESPONSE" | jq -e '.features.git_integration == true' > /dev/null; then
    pass_test "Git Integration" "Enabled"
else
    fail_test "Git Integration" "Should be enabled"
fi

if echo "$ENV_RESPONSE" | jq -e '.features.preview_deployments == true' > /dev/null; then
    pass_test "Preview Deployments" "Enabled"
else
    fail_test "Preview Deployments" "Should be enabled"
fi

# ============================================
# STEP 5: POSTGRES VERIFICATION
# ============================================

section "Step 5: PostgreSQL Database Verification"

info "Checking Postgres connection..."
if docker exec catalyst-postgres pg_isready -U catalyst > /dev/null 2>&1; then
    pass_test "Postgres Connection"
else
    fail_test "Postgres Connection" "Cannot connect"
fi

info "Checking database exists..."
DB_EXISTS=$(docker exec catalyst-postgres psql -U catalyst -lqt | cut -d \| -f 1 | grep -w catalyst_state | wc -l)

if [ "$DB_EXISTS" -eq 1 ]; then
    pass_test "Database catalyst_state exists"
else
    fail_test "Database catalyst_state" "Database not found"
fi

info "Checking tables created..."
TABLES=$(docker exec catalyst-postgres psql -U catalyst -d catalyst_state -c '\dt' -t | wc -l)

if [ "$TABLES" -ge 6 ]; then
    pass_test "Postgres Tables" "$TABLES tables created"
    
    info "Tables found:"
    docker exec catalyst-postgres psql -U catalyst -d catalyst_state -c '\dt' -t | awk '{print "  - " $3}'
else
    fail_test "Postgres Tables" "Expected 6+, found $TABLES"
fi

# ============================================
# STEP 6: RABBITMQ VERIFICATION
# ============================================

section "Step 6: RabbitMQ Event System Verification"

info "Checking RabbitMQ management API..."
if curl -s -u catalyst:catalyst_queue_2025 http://localhost:15672/api/overview > /dev/null; then
    pass_test "RabbitMQ API accessible"
else
    fail_test "RabbitMQ API" "Cannot access management API"
fi

info "Checking queues created..."
QUEUE_COUNT=$(curl -s -u catalyst:catalyst_queue_2025 http://localhost:15672/api/queues | jq '. | length')

if [ "$QUEUE_COUNT" -ge 8 ]; then
    pass_test "RabbitMQ Queues" "$QUEUE_COUNT queues created"
    
    info "Expected queues:"
    curl -s -u catalyst:catalyst_queue_2025 http://localhost:15672/api/queues | jq -r '.[].name' | grep -E 'planner|architect|coder|tester|reviewer|deployer' | while read queue; do
        echo "  ✓ $queue"
    done
else
    fail_test "RabbitMQ Queues" "Expected 8+, found $QUEUE_COUNT"
fi

info "Checking exchange created..."
if curl -s -u catalyst:catalyst_queue_2025 http://localhost:15672/api/exchanges | jq -e '.[] | select(.name == "catalyst.events")' > /dev/null; then
    pass_test "Exchange catalyst.events exists"
else
    fail_test "Exchange catalyst.events" "Not found"
fi

# ============================================
# STEP 7: TRAEFIK VERIFICATION
# ============================================

section "Step 7: Traefik Routing Verification"

info "Checking Traefik dashboard..."
if curl -s http://localhost:8080/api/overview > /dev/null; then
    pass_test "Traefik Dashboard accessible at http://localhost:8080"
else
    fail_test "Traefik Dashboard" "Cannot access"
fi

# ============================================
# STEP 8: BACKEND API TESTS
# ============================================

section "Step 8: Backend API Tests"

info "Testing backend health..."
HEALTH=$(curl -s http://localhost:8001/api/)

if echo "$HEALTH" | jq -e '.message' > /dev/null; then
    pass_test "Backend API Health"
else
    fail_test "Backend API" "No response"
fi

info "Testing chat API..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8001/api/chat/send \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}')

if echo "$CHAT_RESPONSE" | jq -e '.status == "success"' > /dev/null; then
    pass_test "Chat API working"
else
    fail_test "Chat API" "Failed to send message"
fi

info "Testing Git repos API..."
GIT_REPOS=$(curl -s http://localhost:8001/api/git/repos)

if echo "$GIT_REPOS" | jq -e '.success == true' > /dev/null; then
    pass_test "Git Repos API accessible"
else
    fail_test "Git Repos API" "Not working"
fi

info "Testing preview API..."
PREVIEW_API=$(curl -s http://localhost:8001/api/preview)

if echo "$PREVIEW_API" | jq -e '.success == true' > /dev/null; then
    pass_test "Preview API accessible"
else
    fail_test "Preview API" "Not working"
fi

# ============================================
# STEP 9: FRONTEND ACCESS
# ============================================

section "Step 9: Frontend Verification"

info "Testing frontend..."
if curl -s http://localhost:3000 | grep -q "Catalyst"; then
    pass_test "Frontend accessible at http://localhost:3000"
else
    fail_test "Frontend" "Cannot access or Catalyst not found in HTML"
fi

# ============================================
# STEP 10: END-TO-END WORKFLOW TEST
# ============================================

section "Step 10: End-to-End Workflow Test (Optional - Interactive)"

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  MANUAL TESTING REQUIRED${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Please perform the following manual tests:"
echo ""
echo "1. Open Frontend:"
echo "   ${BLUE}http://localhost:3000${NC}"
echo ""
echo "2. Send Build Request:"
echo "   Type: \"build a simple calculator app\""
echo ""
echo "3. Watch for Real-Time Updates:"
echo "   □ See file-level updates (🐍 Generated ...)"
echo "   □ Chat UI grayed out with \"Agent is running...\""
echo "   □ Green pulsing indicator appears"
echo ""
echo "4. Monitor RabbitMQ (Optional):"
echo "   Open: ${BLUE}http://localhost:15672${NC}"
echo "   Login: catalyst / catalyst_queue_2025"
echo "   Watch events flow through queues"
echo ""
echo "5. Wait for Completion (3-5 minutes):"
echo "   Expected final message:"
echo "   \"🎉 Your app is live!\""
echo "   \"   Frontend: http://calculator-app-{id}.localhost\""
echo "   \"   Fallback: http://localhost:9002\""
echo ""
echo "6. Verify Git Repository:"
echo "   ${BLUE}ls -la /app/repos/${NC}"
echo "   Should see: calculator-app/ directory"
echo ""
echo "7. Check Git Commits:"
echo "   ${BLUE}git -C /app/repos/calculator-app/ log --oneline${NC}"
echo "   Should see commits from agents"
echo ""
echo "8. Access Preview (if deployed):"
echo "   ${BLUE}curl http://localhost:9002${NC}"
echo "   Or check: ${BLUE}curl http://localhost:8001/api/preview | jq${NC}"
echo ""
echo "9. Verify Postgres Records:"
echo "   ${BLUE}docker exec -it catalyst-postgres psql -U catalyst -d catalyst_state${NC}"
echo "   Run: ${BLUE}SELECT * FROM tasks ORDER BY created_at DESC LIMIT 1;${NC}"
echo "   Run: ${BLUE}SELECT actor, event_type FROM agent_events ORDER BY created_at DESC LIMIT 10;${NC}"
echo ""
echo "10. Check GitHub (if GITHUB_TOKEN set):"
echo "    Visit: ${BLUE}https://github.com/catalyst-generated/calculator-app${NC}"
echo "    Should see: Code + PR"
echo ""

read -p "Press Enter after completing manual tests to see summary..."

# ============================================
# SUMMARY
# ============================================

section "Test Summary"

echo ""
echo "Automated Tests:"
echo "  ${GREEN}Passed: $PASSED${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo "  ${RED}Failed: $FAILED${NC}"
fi
echo "  Total:  $TOTAL"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL AUTOMATED TESTS PASSED!                                ║${NC}"
    echo -e "${GREEN}║  Infrastructure is working correctly                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Complete manual tests above"
    echo "  2. Report any issues found"
    echo "  3. Ready for Phase 5-6 or production use"
    echo ""
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  SOME TESTS FAILED                                         ║${NC}"
    echo -e "${RED}║  Please review errors above                                    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Docker Desktop has enough resources (4GB+ RAM)"
    echo "  2. Check no port conflicts: lsof -i :5432 (Postgres)"
    echo "  3. View logs: make logs-artifactory"
    echo "  4. Restart: make restart-artifactory"
    echo ""
fi

# ============================================
# USEFUL COMMANDS
# ============================================

section "Useful Commands"

echo "Service Management:"
echo "  ${BLUE}make start-artifactory${NC}        # Start all services"
echo "  ${BLUE}make stop-artifactory${NC}         # Stop all services"
echo "  ${BLUE}make restart-artifactory${NC}      # Restart services"
echo "  ${BLUE}make status-artifactory${NC}       # Show status"
echo "  ${BLUE}make logs-artifactory${NC}         # View logs"
echo ""
echo "Monitoring:"
echo "  ${BLUE}docker ps${NC}                          # See all containers"
echo "  ${BLUE}docker logs catalyst-backend${NC}       # Backend logs"
echo "  ${BLUE}curl http://localhost:8001/api/preview | jq${NC}  # Preview deployments"
echo ""
echo "Database Access:"
echo "  ${BLUE}docker exec -it catalyst-postgres psql -U catalyst -d catalyst_state${NC}"
echo "  ${BLUE}docker exec -it catalyst-mongodb mongosh${NC}"
echo ""
echo "Management UIs:"
echo "  ${BLUE}http://localhost:3000${NC}         # Frontend"
echo "  ${BLUE}http://localhost:8001/docs${NC}    # API Docs"
echo "  ${BLUE}http://localhost:15672${NC}        # RabbitMQ (catalyst/catalyst_queue_2025)"
echo "  ${BLUE}http://localhost:8080${NC}         # Traefik Dashboard"
echo ""
echo "Cleanup:"
echo "  ${BLUE}make fix-all-volumes${NC}          # Clear all data"
echo "  ${BLUE}curl -X POST http://localhost:8001/api/preview/cleanup-expired${NC}  # Cleanup previews"
echo ""

echo -e "${GREEN}Testing script complete!${NC}"
echo ""

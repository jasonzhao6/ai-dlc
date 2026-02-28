#!/bin/bash
# End-to-end test runner
#
# Prerequisites:
#   1. Docker running
#   2. DynamoDB Local on port 8000:
#        docker run -d --name dynamodb-local --network sam-network -p 8000:8000 amazon/dynamodb-local
#   3. SAM app built:
#        sam build
#   4. Python packages: pip install bcrypt boto3
#
# Usage:
#   bash tests/run_e2e.sh

set -e

TABLE_NAME="FileShareTable-dev"
ENDPOINT="http://localhost:8000"
REGION="us-east-1"
API_URL="http://127.0.0.1:3000"
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_PAGER=""

SAM_PID=""

cleanup() {
    if [ -n "$SAM_PID" ]; then
        echo ""
        echo ">>> Stopping SAM local API (pid $SAM_PID)..."
        kill "$SAM_PID" 2>/dev/null || true
        wait "$SAM_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# ------------------------------------------------------------------
# Start SAM local API if not already running
# ------------------------------------------------------------------
if curl -s -o /dev/null http://127.0.0.1:3000 2>/dev/null; then
    echo ">>> SAM local API already running on port 3000"
else
    echo ">>> Starting SAM local API..."
    sam local start-api \
        --docker-network sam-network \
        --env-vars tests/local-env.json \
        --warm-containers EAGER > /tmp/sam-local-api.log 2>&1 &
    SAM_PID=$!

    echo ">>> Waiting for SAM local API to be ready..."
    for i in $(seq 1 60); do
        if curl -s -o /dev/null http://127.0.0.1:3000 2>/dev/null; then
            echo ">>> SAM local API ready after ${i}s"
            break
        fi
        if ! kill -0 "$SAM_PID" 2>/dev/null; then
            echo ">>> ERROR: SAM local API failed to start. Check /tmp/sam-local-api.log"
            exit 1
        fi
        sleep 1
    done

    if ! curl -s -o /dev/null http://127.0.0.1:3000 2>/dev/null; then
        echo ">>> ERROR: SAM local API did not become ready within 60s"
        exit 1
    fi
fi

# ------------------------------------------------------------------
# Helper: reset DynamoDB and seed admin user
# ------------------------------------------------------------------
reset_db() {
    echo ">>> Resetting DynamoDB table..."
    aws dynamodb delete-table \
        --table-name "$TABLE_NAME" \
        --endpoint-url "$ENDPOINT" \
        --region "$REGION" 2>/dev/null || true
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=PK,AttributeType=S \
            AttributeName=SK,AttributeType=S \
            AttributeName=GSI1PK,AttributeType=S \
            AttributeName=GSI1SK,AttributeType=S \
        --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
        --global-secondary-indexes \
            'IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url "$ENDPOINT" \
        --region "$REGION" > /dev/null 2>&1
    echo ">>> Seeding admin user..."
    python3 tests/seed_admin.py
}

# ------------------------------------------------------------------
# Run a single test suite
# ------------------------------------------------------------------
TOTAL_PASS=0
TOTAL_FAIL=0

run_suite() {
    local suite="$1"
    echo ""
    echo "============================================================"
    echo "  Running: $suite"
    echo "============================================================"
    reset_db
    output=$(python3 "$suite" 2>&1)
    echo "$output"
    # Extract pass/fail counts from last line matching "Results:"
    local pass_count=$(echo "$output" | grep "Results:" | grep -o '[0-9]* passed' | grep -o '[0-9]*')
    local fail_count=$(echo "$output" | grep "Results:" | grep -o '[0-9]* failed' | grep -o '[0-9]*')
    TOTAL_PASS=$((TOTAL_PASS + ${pass_count:-0}))
    TOTAL_FAIL=$((TOTAL_FAIL + ${fail_count:-0}))
}

# ------------------------------------------------------------------
# Run all suites
# ------------------------------------------------------------------
run_suite "tests/test_auth_users.py"
run_suite "tests/test_folders.py"
run_suite "tests/test_files.py"
run_suite "tests/test_search.py"

echo ""
echo "============================================================"
echo "  FINAL E2E RESULTS: $TOTAL_PASS passed, $TOTAL_FAIL failed"
echo "============================================================"

if [ "$TOTAL_FAIL" -gt 0 ]; then
    exit 1
fi
echo "All end-to-end tests passed!"

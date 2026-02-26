#!/bin/bash
# End-to-end test runner: resets DynamoDB between test suites

set -e

TABLE_NAME="FileShareTable-dev"
ENDPOINT="http://localhost:8000"
REGION="us-east-1"
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy

reset_db() {
    echo ">>> Resetting DynamoDB table..."
    aws dynamodb delete-table --table-name "$TABLE_NAME" --endpoint-url "$ENDPOINT" --region "$REGION" 2>/dev/null || true
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
    sam local invoke SeedFunction --docker-network sam-network --env-vars tests/local-env.json --no-event 2>&1 | grep -o '"created": [a-z]*'
}

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

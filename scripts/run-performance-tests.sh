#!/bin/bash

# Performance Testing Suite for TradeSense
# Runs comprehensive performance tests and generates reports

set -e

# Configuration
TEST_TYPE="${1:-load}"  # load, stress, spike, soak, all
DURATION="${2:-10m}"
USERS="${3:-100}"
SPAWN_RATE="${4:-10}"
TARGET_HOST="${TARGET_HOST:-http://localhost:8000}"
RESULTS_DIR="./performance-results/$(date +%Y%m%d_%H%M%S)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing+=("docker-compose")
    fi
    
    # Check if backend is running
    if ! curl -s -o /dev/null -w "%{http_code}" "$TARGET_HOST/health" | grep -q "200"; then
        print_warning "Backend service not accessible at $TARGET_HOST"
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing prerequisites: ${missing[*]}"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Run Locust tests
run_locust_test() {
    local test_name=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    
    print_status "Running Locust $test_name test..."
    
    # Start Locust in headless mode
    docker run --rm \
        --network host \
        -v "$(pwd)/tests/performance:/mnt/locust" \
        -v "$RESULTS_DIR:/results" \
        locustio/locust \
        -f /mnt/locust/locustfile.py \
        --headless \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$duration" \
        --host "$TARGET_HOST" \
        --html "/results/locust_${test_name}_report.html" \
        --csv "/results/locust_${test_name}" \
        --loglevel INFO
    
    print_success "Locust $test_name test completed"
}

# Run K6 tests
run_k6_test() {
    local test_name=$1
    
    print_status "Running K6 $test_name test..."
    
    # Run K6 with specific scenario
    docker run --rm \
        --network host \
        -v "$(pwd)/tests/performance:/scripts" \
        -v "$RESULTS_DIR:/results" \
        -e BASE_URL="$TARGET_HOST" \
        grafana/k6 run \
        --out json="/results/k6_${test_name}_results.json" \
        --summary-export="/results/k6_${test_name}_summary.json" \
        /scripts/k6-test.js
    
    print_success "K6 $test_name test completed"
}

# Run Apache Bench test
run_ab_test() {
    local endpoint=$1
    local requests=${2:-1000}
    local concurrency=${3:-100}
    
    print_status "Running Apache Bench test on $endpoint..."
    
    docker run --rm \
        --network host \
        httpd:alpine \
        ab -n "$requests" -c "$concurrency" \
        -g "$RESULTS_DIR/ab_${endpoint//\//_}.tsv" \
        "$TARGET_HOST$endpoint" \
        > "$RESULTS_DIR/ab_${endpoint//\//_}.txt"
    
    print_success "Apache Bench test completed"
}

# Run database performance test
run_database_test() {
    print_status "Running database performance test..."
    
    # Use pgbench for PostgreSQL performance testing
    docker run --rm \
        --network tradesense_default \
        -e PGPASSWORD="${POSTGRES_PASSWORD}" \
        postgres:15 \
        pgbench -h postgres -U tradesense -d tradesense \
        -c 10 -j 2 -t 1000 \
        > "$RESULTS_DIR/pgbench_results.txt"
    
    print_success "Database performance test completed"
}

# Monitor system resources during tests
monitor_resources() {
    local duration=$1
    local output_file="$RESULTS_DIR/resource_usage.csv"
    
    print_status "Starting resource monitoring..."
    
    echo "timestamp,cpu_percent,memory_percent,disk_io_read,disk_io_write,network_sent,network_recv" > "$output_file"
    
    # Monitor in background
    (
        end_time=$(($(date +%s) + ${duration%m} * 60))
        while [ $(date +%s) -lt $end_time ]; do
            timestamp=$(date +%s)
            cpu=$(docker stats --no-stream --format "{{.CPUPerc}}" tradesense-backend-1 | sed 's/%//')
            memory=$(docker stats --no-stream --format "{{.MemPerc}}" tradesense-backend-1 | sed 's/%//')
            
            echo "$timestamp,$cpu,$memory,0,0,0,0" >> "$output_file"
            sleep 5
        done
    ) &
    
    MONITOR_PID=$!
}

# Generate performance report
generate_report() {
    print_status "Generating performance report..."
    
    cat > "$RESULTS_DIR/performance_report.md" << EOF
# TradeSense Performance Test Report

**Date:** $(date)
**Test Type:** $TEST_TYPE
**Duration:** $DURATION
**Target:** $TARGET_HOST

## Test Configuration
- Maximum Users: $USERS
- Spawn Rate: $SPAWN_RATE users/second

## Test Results

### Response Time Statistics
EOF

    # Parse Locust results if available
    if ls "$RESULTS_DIR"/locust_*_stats.csv 1> /dev/null 2>&1; then
        echo -e "\n### Locust Results\n" >> "$RESULTS_DIR/performance_report.md"
        echo '```' >> "$RESULTS_DIR/performance_report.md"
        cat "$RESULTS_DIR"/locust_*_stats.csv | column -t -s, >> "$RESULTS_DIR/performance_report.md"
        echo '```' >> "$RESULTS_DIR/performance_report.md"
    fi

    # Parse K6 results if available
    if [ -f "$RESULTS_DIR/k6_${TEST_TYPE}_summary.json" ]; then
        echo -e "\n### K6 Results\n" >> "$RESULTS_DIR/performance_report.md"
        jq -r '.metrics | to_entries | .[] | "\(.key): \(.value.avg // .value.value)"' \
            "$RESULTS_DIR/k6_${TEST_TYPE}_summary.json" >> "$RESULTS_DIR/performance_report.md"
    fi

    # Add recommendations
    cat >> "$RESULTS_DIR/performance_report.md" << EOF

## Recommendations

1. **Response Times**: Aim for p95 < 500ms for API endpoints
2. **Error Rate**: Keep error rate below 1%
3. **Throughput**: Current system can handle X requests/second
4. **Database**: Consider connection pooling optimization
5. **Caching**: Redis hit rate should be > 80%

## Next Steps

- [ ] Optimize slow endpoints identified in the report
- [ ] Implement caching for frequently accessed data
- [ ] Scale horizontally if needed
- [ ] Set up continuous performance monitoring
EOF

    print_success "Performance report generated: $RESULTS_DIR/performance_report.md"
}

# Main test execution
main() {
    print_status "Starting TradeSense Performance Testing Suite"
    echo "============================================"
    
    check_prerequisites
    
    # Start resource monitoring
    monitor_resources "$DURATION"
    
    case "$TEST_TYPE" in
        "load")
            run_locust_test "load" "$USERS" "$SPAWN_RATE" "$DURATION"
            ;;
        "stress")
            run_locust_test "stress" $((USERS * 2)) $((SPAWN_RATE * 2)) "$DURATION"
            ;;
        "spike")
            run_k6_test "spike"
            ;;
        "soak")
            run_locust_test "soak" 50 5 "30m"
            ;;
        "api")
            # Test specific API endpoints
            run_ab_test "/api/v1/analytics/dashboard" 1000 50
            run_ab_test "/api/v1/trades" 1000 100
            run_ab_test "/api/v1/auth/login" 100 10
            ;;
        "database")
            run_database_test
            ;;
        "all")
            run_locust_test "load" "$USERS" "$SPAWN_RATE" "5m"
            run_locust_test "stress" $((USERS * 2)) $((SPAWN_RATE * 2)) "5m"
            run_k6_test "complete"
            run_database_test
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            echo "Available types: load, stress, spike, soak, api, database, all"
            exit 1
            ;;
    esac
    
    # Stop resource monitoring
    if [ -n "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi
    
    # Generate report
    generate_report
    
    print_status "Performance testing completed!"
    echo -e "\nResults saved to: ${GREEN}$RESULTS_DIR${NC}"
    echo -e "View report: ${GREEN}$RESULTS_DIR/performance_report.md${NC}"
    
    # Open HTML report if available
    if ls "$RESULTS_DIR"/*.html 1> /dev/null 2>&1; then
        echo -e "\nHTML reports available:"
        ls -1 "$RESULTS_DIR"/*.html
    fi
}

# Handle script termination
trap 'kill $MONITOR_PID 2>/dev/null || true' EXIT

# Run main function
main
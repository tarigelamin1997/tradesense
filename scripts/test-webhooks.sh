#!/bin/bash

# Stripe Webhook Testing Script
# This script helps test webhook handling locally using the Stripe CLI

echo "🔧 TradeSense Stripe Webhook Testing"
echo "===================================="

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI is not installed. Please install it first:"
    echo "   brew install stripe/stripe-cli/stripe (macOS)"
    echo "   or visit: https://stripe.com/docs/stripe-cli"
    exit 1
fi

# Configuration
WEBHOOK_ENDPOINT="http://localhost:8000/api/v1/billing/webhook"
LOG_FILE="webhook_test_results.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test a webhook event
test_webhook_event() {
    local event_type=$1
    local description=$2
    
    echo -e "\n${YELLOW}Testing: ${description}${NC}"
    echo "Event: ${event_type}"
    echo "---"
    
    # Trigger the event
    stripe trigger ${event_type} >> ${LOG_FILE} 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Event triggered successfully${NC}"
    else
        echo -e "${RED}✗ Failed to trigger event${NC}"
        echo "Check ${LOG_FILE} for details"
    fi
    
    # Give the webhook time to process
    sleep 2
}

# Main testing flow
main() {
    echo "Starting webhook endpoint listener..."
    echo "Endpoint: ${WEBHOOK_ENDPOINT}"
    echo ""
    
    # Start listening in background
    echo "Starting Stripe webhook forwarding..."
    stripe listen --forward-to ${WEBHOOK_ENDPOINT} &
    STRIPE_PID=$!
    
    # Give it time to start
    sleep 3
    
    echo -e "\n${GREEN}Webhook listener started (PID: ${STRIPE_PID})${NC}"
    echo "Running test scenarios..."
    
    # Test Scenario 1: Successful Checkout
    echo -e "\n${YELLOW}=== Scenario 1: Successful Checkout ===${NC}"
    test_webhook_event "checkout.session.completed" "Customer completes checkout"
    test_webhook_event "customer.subscription.created" "Subscription created"
    test_webhook_event "invoice.payment_succeeded" "First payment succeeds"
    
    # Test Scenario 2: Payment Failure
    echo -e "\n${YELLOW}=== Scenario 2: Payment Failure ===${NC}"
    test_webhook_event "invoice.payment_failed" "Payment fails (card declined)"
    test_webhook_event "customer.subscription.updated" "Subscription marked as past_due"
    
    # Test Scenario 3: Subscription Changes
    echo -e "\n${YELLOW}=== Scenario 3: Subscription Management ===${NC}"
    test_webhook_event "customer.subscription.updated" "Customer upgrades plan"
    test_webhook_event "customer.subscription.deleted" "Customer cancels subscription"
    
    # Test Scenario 4: Trial Events
    echo -e "\n${YELLOW}=== Scenario 4: Trial Management ===${NC}"
    test_webhook_event "customer.subscription.trial_will_end" "Trial ending soon"
    
    # Test Scenario 5: Edge Cases
    echo -e "\n${YELLOW}=== Scenario 5: Edge Cases ===${NC}"
    test_webhook_event "charge.dispute.created" "Chargeback initiated"
    
    # Cleanup
    echo -e "\n${YELLOW}Stopping webhook listener...${NC}"
    kill ${STRIPE_PID} 2>/dev/null
    
    echo -e "\n${GREEN}✅ Webhook testing complete!${NC}"
    echo "Check ${LOG_FILE} for detailed results"
    
    # Show summary
    echo -e "\n${YELLOW}=== Test Summary ===${NC}"
    echo "Events tested: 9"
    echo "Log file: ${LOG_FILE}"
    echo ""
    echo "Next steps:"
    echo "1. Check your database for created subscriptions"
    echo "2. Verify webhook signatures are validated"
    echo "3. Test with production webhook endpoint"
}

# Run tests
main

# Optional: Show recent logs
echo -e "\n${YELLOW}Recent webhook logs:${NC}"
tail -20 ${LOG_FILE}
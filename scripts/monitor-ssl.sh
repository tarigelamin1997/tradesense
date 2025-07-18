#!/bin/bash

# SSL/TLS Certificate Monitoring Script for TradeSense
# This script monitors SSL certificate expiration and health

set -e

# Configuration
DOMAINS="${DOMAINS:-tradesense.com www.tradesense.com api.tradesense.com}"
ALERT_DAYS="${ALERT_DAYS:-30}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL="${EMAIL:-admin@tradesense.com}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check certificate expiration
check_cert_expiration() {
    local domain=$1
    local port=${2:-443}
    
    echo -e "\n${YELLOW}Checking certificate for $domain:$port...${NC}"
    
    # Get certificate expiration date
    cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to retrieve certificate for $domain${NC}"
        return 1
    fi
    
    # Extract dates
    not_before=$(echo "$cert_info" | grep "notBefore" | cut -d= -f2)
    not_after=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
    
    # Convert to timestamps
    not_after_timestamp=$(date -d "$not_after" +%s)
    current_timestamp=$(date +%s)
    
    # Calculate days until expiration
    days_until_expiry=$(( (not_after_timestamp - current_timestamp) / 86400 ))
    
    echo "Certificate valid from: $not_before"
    echo "Certificate expires on: $not_after"
    echo "Days until expiration: $days_until_expiry"
    
    # Check if certificate is expiring soon
    if [ $days_until_expiry -lt 0 ]; then
        echo -e "${RED}❌ Certificate has EXPIRED!${NC}"
        send_alert "CRITICAL" "$domain" "Certificate has expired!" "$days_until_expiry"
        return 2
    elif [ $days_until_expiry -lt $ALERT_DAYS ]; then
        echo -e "${YELLOW}⚠️  Certificate expiring soon!${NC}"
        send_alert "WARNING" "$domain" "Certificate expiring in $days_until_expiry days" "$days_until_expiry"
        return 1
    else
        echo -e "${GREEN}✅ Certificate is valid${NC}"
        return 0
    fi
}

# Function to check certificate chain
check_cert_chain() {
    local domain=$1
    local port=${2:-443}
    
    echo -e "\n${YELLOW}Checking certificate chain for $domain...${NC}"
    
    # Get full certificate chain
    chain=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" -showcerts 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to retrieve certificate chain${NC}"
        return 1
    fi
    
    # Count certificates in chain
    cert_count=$(echo "$chain" | grep -c "BEGIN CERTIFICATE")
    
    echo "Certificates in chain: $cert_count"
    
    if [ $cert_count -lt 2 ]; then
        echo -e "${YELLOW}⚠️  Certificate chain may be incomplete${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Certificate chain is complete${NC}"
        return 0
    fi
}

# Function to check SSL/TLS configuration
check_ssl_config() {
    local domain=$1
    local port=${2:-443}
    
    echo -e "\n${YELLOW}Checking SSL/TLS configuration for $domain...${NC}"
    
    # Check supported protocols
    echo "Checking supported protocols..."
    for protocol in ssl2 ssl3 tls1 tls1_1 tls1_2 tls1_3; do
        result=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" -$protocol 2>&1)
        if echo "$result" | grep -q "CONNECTED"; then
            if [[ "$protocol" == "ssl2" || "$protocol" == "ssl3" || "$protocol" == "tls1" || "$protocol" == "tls1_1" ]]; then
                echo -e "${RED}❌ $protocol is ENABLED (insecure)${NC}"
            else
                echo -e "${GREEN}✅ $protocol is enabled${NC}"
            fi
        else
            if [[ "$protocol" == "tls1_2" || "$protocol" == "tls1_3" ]]; then
                echo -e "${YELLOW}⚠️  $protocol is disabled${NC}"
            else
                echo -e "${GREEN}✅ $protocol is disabled (good)${NC}"
            fi
        fi
    done
    
    # Check cipher strength
    echo -e "\nChecking cipher strength..."
    ciphers=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" -cipher 'HIGH:!aNULL:!MD5' 2>/dev/null | grep "Cipher")
    echo "$ciphers"
}

# Function to check OCSP stapling
check_ocsp_stapling() {
    local domain=$1
    local port=${2:-443}
    
    echo -e "\n${YELLOW}Checking OCSP stapling for $domain...${NC}"
    
    ocsp_response=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" -status 2>/dev/null | grep -A 20 "OCSP Response Status")
    
    if echo "$ocsp_response" | grep -q "successful"; then
        echo -e "${GREEN}✅ OCSP stapling is enabled${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  OCSP stapling is not enabled${NC}"
        return 1
    fi
}

# Function to send alerts
send_alert() {
    local severity=$1
    local domain=$2
    local message=$3
    local days=$4
    
    # Send Slack notification if webhook is configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"SSL Certificate Alert\",\"attachments\":[{\"color\":\"$([ "$severity" = "CRITICAL" ] && echo "danger" || echo "warning")\",\"title\":\"$severity: $domain\",\"text\":\"$message\",\"fields\":[{\"title\":\"Days until expiry\",\"value\":\"$days\",\"short\":true}]}]}" \
            "$SLACK_WEBHOOK" 2>/dev/null
    fi
    
    # Send email notification
    if command -v mail &> /dev/null && [ -n "$EMAIL" ]; then
        echo -e "Subject: SSL Certificate Alert - $severity: $domain\n\n$message\n\nDays until expiry: $days" | mail -s "SSL Certificate Alert - $severity: $domain" "$EMAIL"
    fi
    
    # Log to file
    echo "[$(date)] $severity: $domain - $message (Days: $days)" >> /var/log/ssl-monitor.log
}

# Function to generate SSL report
generate_report() {
    local report_file="/var/log/ssl-monitor-report-$(date +%Y%m%d_%H%M%S).txt"
    
    echo -e "\n${YELLOW}Generating SSL monitoring report...${NC}"
    
    {
        echo "SSL/TLS Monitoring Report"
        echo "========================="
        echo "Date: $(date)"
        echo "Monitored domains: $DOMAINS"
        echo ""
        
        for domain in $DOMAINS; do
            echo "Domain: $domain"
            echo "----------------"
            
            # Get certificate info
            cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
            
            # Extract key information
            echo "$cert_info" | grep -E "(Subject:|Issuer:|Not Before:|Not After:|Signature Algorithm:|Public Key Algorithm:)" || echo "Failed to retrieve certificate"
            
            echo ""
        done
        
        echo "Recommendations:"
        echo "1. Renew certificates at least 30 days before expiration"
        echo "2. Use automated renewal with Let's Encrypt"
        echo "3. Monitor certificate transparency logs"
        echo "4. Implement HSTS and CAA records"
        echo "5. Regular security audits with SSL Labs"
        
    } > "$report_file"
    
    echo -e "${GREEN}✅ Report generated: $report_file${NC}"
}

# Main monitoring function
main() {
    echo "🔒 SSL/TLS Certificate Monitoring"
    echo "================================="
    echo "Domains: $DOMAINS"
    echo "Alert threshold: $ALERT_DAYS days"
    echo ""
    
    local exit_code=0
    
    for domain in $DOMAINS; do
        check_cert_expiration "$domain" || exit_code=$?
        check_cert_chain "$domain"
        check_ssl_config "$domain"
        check_ocsp_stapling "$domain"
    done
    
    generate_report
    
    if [ $exit_code -eq 0 ]; then
        echo -e "\n${GREEN}✅ All SSL certificates are healthy${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Some issues were found${NC}"
    fi
    
    return $exit_code
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domains)
            DOMAINS="$2"
            shift 2
            ;;
        --alert-days)
            ALERT_DAYS="$2"
            shift 2
            ;;
        --slack-webhook)
            SLACK_WEBHOOK="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --domains DOMAINS         Space-separated list of domains to monitor"
            echo "  --alert-days DAYS        Days before expiry to send alerts (default: 30)"
            echo "  --slack-webhook URL      Slack webhook URL for notifications"
            echo "  --email EMAIL           Email address for notifications"
            echo "  --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main
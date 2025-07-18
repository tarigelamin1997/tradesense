#!/bin/bash

# SSL/TLS Setup Script for TradeSense
# This script configures SSL certificates using Let's Encrypt

set -e

echo "🔒 Setting up SSL/TLS for TradeSense..."
echo "======================================"

# Configuration
DOMAIN="${DOMAIN:-tradesense.com}"
EMAIL="${EMAIL:-admin@tradesense.com}"
STAGING="${STAGING:-false}"
NGINX_CONFIG_PATH="/etc/nginx"
SSL_PATH="/etc/nginx/ssl"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root${NC}"
        exit 1
    fi
}

# Function to install certbot
install_certbot() {
    echo -e "\n${YELLOW}Installing Certbot...${NC}"
    
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        yum install -y epel-release
        yum install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}Unsupported OS. Please install certbot manually.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Certbot installed${NC}"
}

# Function to create SSL directory
create_ssl_directory() {
    echo -e "\n${YELLOW}Creating SSL directory...${NC}"
    mkdir -p $SSL_PATH
    chmod 755 $SSL_PATH
    echo -e "${GREEN}✅ SSL directory created${NC}"
}

# Function to generate DH parameters
generate_dhparam() {
    echo -e "\n${YELLOW}Generating DH parameters (this may take a while)...${NC}"
    
    if [ ! -f "$SSL_PATH/dhparam.pem" ]; then
        openssl dhparam -out $SSL_PATH/dhparam.pem 2048
        echo -e "${GREEN}✅ DH parameters generated${NC}"
    else
        echo -e "${GREEN}✅ DH parameters already exist${NC}"
    fi
}

# Function to create nginx SSL configuration
create_nginx_ssl_config() {
    echo -e "\n${YELLOW}Creating Nginx SSL configuration...${NC}"
    
    cat > $NGINX_CONFIG_PATH/snippets/ssl-params.conf << 'EOF'
# SSL Parameters
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# SSL Session
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;

# Security Headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.stripe.com wss://$server_name ws://$server_name" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(self)" always;

# DH Parameters
ssl_dhparam /etc/nginx/ssl/dhparam.pem;

# Resolver
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
    
    echo -e "${GREEN}✅ Nginx SSL configuration created${NC}"
}

# Function to obtain SSL certificate
obtain_certificate() {
    echo -e "\n${YELLOW}Obtaining SSL certificate...${NC}"
    
    CERTBOT_FLAGS=""
    if [ "$STAGING" = "true" ]; then
        CERTBOT_FLAGS="--staging"
        echo -e "${YELLOW}Using Let's Encrypt staging environment${NC}"
    fi
    
    # Stop nginx temporarily
    systemctl stop nginx || true
    
    # Obtain certificate
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        -d $DOMAIN \
        -d www.$DOMAIN \
        $CERTBOT_FLAGS
    
    # Start nginx
    systemctl start nginx
    
    echo -e "${GREEN}✅ SSL certificate obtained${NC}"
}

# Function to configure nginx for SSL
configure_nginx_ssl() {
    echo -e "\n${YELLOW}Configuring Nginx for SSL...${NC}"
    
    # Backup existing configuration
    cp $NGINX_CONFIG_PATH/sites-available/tradesense \
       $NGINX_CONFIG_PATH/sites-available/tradesense.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update nginx configuration to use Let's Encrypt certificates
    sed -i "s|ssl_certificate .*|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|" \
        $NGINX_CONFIG_PATH/sites-available/tradesense
    sed -i "s|ssl_certificate_key .*|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|" \
        $NGINX_CONFIG_PATH/sites-available/tradesense
    
    # Add include for SSL parameters
    if ! grep -q "include /etc/nginx/snippets/ssl-params.conf;" $NGINX_CONFIG_PATH/sites-available/tradesense; then
        sed -i '/listen 443 ssl http2;/a\    include /etc/nginx/snippets/ssl-params.conf;' \
            $NGINX_CONFIG_PATH/sites-available/tradesense
    fi
    
    echo -e "${GREEN}✅ Nginx configured for SSL${NC}"
}

# Function to setup auto-renewal
setup_auto_renewal() {
    echo -e "\n${YELLOW}Setting up auto-renewal...${NC}"
    
    # Create renewal hook script
    cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
    
    # Test renewal
    certbot renew --dry-run
    
    # Add cron job if it doesn't exist
    if ! crontab -l | grep -q "certbot renew"; then
        (crontab -l 2>/dev/null; echo "0 2,14 * * * /usr/bin/certbot renew --quiet") | crontab -
    fi
    
    echo -e "${GREEN}✅ Auto-renewal configured${NC}"
}

# Function to test SSL configuration
test_ssl_configuration() {
    echo -e "\n${YELLOW}Testing SSL configuration...${NC}"
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    # Test SSL connection
    echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | \
        openssl x509 -noout -dates
    
    echo -e "${GREEN}✅ SSL configuration test passed${NC}"
}

# Function to generate SSL security report
generate_ssl_report() {
    echo -e "\n${YELLOW}Generating SSL security report...${NC}"
    
    REPORT_FILE="/var/log/ssl-setup-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > $REPORT_FILE << EOF
SSL/TLS Setup Report for TradeSense
===================================
Date: $(date)
Domain: $DOMAIN

Certificate Information:
$(certbot certificates 2>/dev/null | grep -A 5 "$DOMAIN")

SSL Configuration Test:
$(echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -text | grep -E "(Subject:|Issuer:|Not Before:|Not After:)")

Nginx SSL Configuration:
$(nginx -T 2>/dev/null | grep -E "(ssl_|listen 443)")

Security Headers Test:
$(curl -sI https://$DOMAIN | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options|Content-Security-Policy)")

Next Steps:
1. Test your SSL configuration at: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN
2. Monitor certificate expiration
3. Review security headers
4. Enable CAA records in DNS

Auto-Renewal Status:
$(systemctl status certbot.timer 2>/dev/null || echo "Cron-based renewal configured")
EOF
    
    echo -e "${GREEN}✅ SSL report generated: $REPORT_FILE${NC}"
}

# Main execution
main() {
    echo "Domain: $DOMAIN"
    echo "Email: $EMAIL"
    echo "Staging: $STAGING"
    echo ""
    
    check_root
    install_certbot
    create_ssl_directory
    generate_dhparam
    create_nginx_ssl_config
    obtain_certificate
    configure_nginx_ssl
    setup_auto_renewal
    test_ssl_configuration
    generate_ssl_report
    
    echo -e "\n${GREEN}🎉 SSL/TLS setup completed successfully!${NC}"
    echo -e "\nNext steps:"
    echo "1. Test your SSL configuration at: https://www.ssllabs.com/ssltest/"
    echo "2. Update your DNS records if needed"
    echo "3. Monitor certificate renewal"
    echo "4. Review the SSL report"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --staging)
            STAGING="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --domain DOMAIN   Domain name (default: tradesense.com)"
            echo "  --email EMAIL     Email for Let's Encrypt (default: admin@tradesense.com)"
            echo "  --staging         Use Let's Encrypt staging environment"
            echo "  --help            Show this help message"
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
#!/bin/bash

# VPN Management API - One Click Installer
# Installer untuk API management VPN services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# GitHub repository
GITHUB_REPO="alrel1408/API"
GITHUB_RAW="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

# Function to print colored output
print_ok() {
    echo -e "[${GREEN}OK${NC}] $1"
}

print_error() {
    echo -e "[${RED}ERROR${NC}] $1"
}

print_warning() {
    echo -e "[${YELLOW}WARNING${NC}] $1"
}

print_info() {
    echo -e "[${BLUE}INFO${NC}] $1"
}

# Function to check command result
check_result() {
    if [ $? -eq 0 ]; then
        print_ok "$1"
    else
        print_error "$2"
        exit 1
    fi
}

# Banner
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              VPN MANAGEMENT API          ║${NC}"
echo -e "${CYAN}║           ONE CLICK INSTALLER v1.0       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

print_info "Installing VPN Management API from GitHub..."

# Check internet connection
print_info "Checking internet connection..."
curl -s --max-time 10 google.com > /dev/null
check_result "Internet connection OK" "No internet connection"

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
    print_info "Detected OS: Debian/Ubuntu"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    print_info "Detected OS: RedHat/CentOS"
else
    print_error "Unsupported OS"
    exit 1
fi

# Update system
print_info "Updating system packages..."
if [[ "$OS" == "debian" ]]; then
    apt update >/dev/null 2>&1
    check_result "System packages updated" "Failed to update packages"
else
    yum update -y >/dev/null 2>&1
    check_result "System packages updated" "Failed to update packages"
fi

# Install dependencies
print_info "Installing required dependencies..."
if [[ "$OS" == "debian" ]]; then
    apt install -y curl wget python3 python3-pip nginx supervisor >/dev/null 2>&1
    check_result "Dependencies installed" "Failed to install dependencies"
else
    yum install -y curl wget python3 python3-pip nginx supervisor >/dev/null 2>&1
    check_result "Dependencies installed" "Failed to install dependencies"
fi

# Install Python packages
print_info "Installing Python packages..."
pip3 install flask flask-limiter gunicorn >/dev/null 2>&1
check_result "Python packages installed" "Failed to install Python packages"

# Test gunicorn installation
print_info "Testing gunicorn installation..."
if python3 -m gunicorn --version >/dev/null 2>&1; then
    print_ok "Gunicorn is available"
    USE_GUNICORN=true
else
    print_warning "Gunicorn not available, using direct Python execution"
    USE_GUNICORN=false
fi

# Create directories
print_info "Creating directories..."
mkdir -p /etc/API
mkdir -p /var/log/api
mkdir -p /var/www/html
check_result "Directories created" "Failed to create directories"

# Download main API file
print_info "Downloading VPN API main file..."
curl -sL "$GITHUB_RAW/vpn_api.py" -o /etc/API/vpn_api.py
check_result "API file downloaded" "Failed to download API file"

# Download service modules
print_info "Downloading service modules..."
curl -sL "$GITHUB_RAW/ssh_service.py" -o /etc/API/ssh_service.py
curl -sL "$GITHUB_RAW/trojan_service.py" -o /etc/API/trojan_service.py
curl -sL "$GITHUB_RAW/vmess_service.py" -o /etc/API/vmess_service.py
curl -sL "$GITHUB_RAW/vless_service.py" -o /etc/API/vless_service.py
curl -sL "$GITHUB_RAW/trial_service.py" -o /etc/API/trial_service.py
check_result "Service modules downloaded" "Failed to download service modules"

# Download management scripts
print_info "Downloading management scripts..."
curl -sL "$GITHUB_RAW/manage_api.sh" -o /etc/API/manage_api.sh
curl -sL "$GITHUB_RAW/test_api.sh" -o /etc/API/test_api.sh
curl -sL "$GITHUB_RAW/uninstall_api.sh" -o /etc/API/uninstall_api.sh
check_result "Management scripts downloaded" "Failed to download management scripts"

# Download documentation
print_info "Downloading documentation..."
curl -sL "$GITHUB_RAW/README.md" -o /etc/API/README.md
curl -sL "$GITHUB_RAW/API_DOCUMENTATION.md" -o /etc/API/API_DOCUMENTATION.md
check_result "Documentation downloaded" "Failed to download documentation"

# Set permissions
chmod +x /etc/API/*.sh
chmod +x /etc/API/*.py
check_result "Permissions set" "Failed to set permissions"

# Generate default API key
print_info "Generating API configuration..."
DEFAULT_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create API keys file
cat > /etc/API/api_keys.json << EOF
{
  "keys": [
    {
      "key": "$DEFAULT_API_KEY",
      "name": "default",
      "created": "$(date -Iseconds)",
      "active": true
    }
  ]
}
EOF
check_result "API keys generated" "Failed to generate API keys"

# Create systemd service
print_info "Creating systemd service..."
if [ "$USE_GUNICORN" = true ]; then
    cat > /etc/systemd/system/vpn-api.service << 'EOF'
[Unit]
Description=VPN Management API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/etc/API
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH=/etc/API
ExecStart=/usr/bin/python3 -m gunicorn --bind 0.0.0.0:7777 --workers 2 --timeout 120 vpn_api:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
else
    cat > /etc/systemd/system/vpn-api.service << 'EOF'
[Unit]
Description=VPN Management API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/etc/API
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH=/etc/API
ExecStart=/usr/bin/python3 /etc/API/vpn_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
fi
check_result "Systemd service created" "Failed to create systemd service"

# Configure Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/vpn-api << 'EOF'
server {
    listen 7777;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:7777;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable Nginx site
if [ -d "/etc/nginx/sites-enabled" ]; then
    ln -sf /etc/nginx/sites-available/vpn-api /etc/nginx/sites-enabled/
else
    # For systems without sites-enabled (like CentOS)
    echo "include /etc/nginx/sites-available/vpn-api;" >> /etc/nginx/nginx.conf
fi

# Test Nginx configuration
nginx -t >/dev/null 2>&1
check_result "Nginx configured" "Failed to configure Nginx"

# Create management command
print_info "Creating management command..."
cat > /usr/local/bin/vpn-api << 'EOF'
#!/bin/bash
/etc/API/manage_api.sh "$@"
EOF
chmod +x /usr/local/bin/vpn-api
check_result "Management command created" "Failed to create management command"

# Configure firewall
print_info "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 7777/tcp >/dev/null 2>&1
    print_ok "UFW rule added for port 7777"
elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=7777/tcp >/dev/null 2>&1
    firewall-cmd --reload >/dev/null 2>&1
    print_ok "Firewalld rule added for port 7777"
else
    print_warning "No supported firewall found, ensure port 7777 is open"
fi

# Enable and start services
print_info "Starting services..."
systemctl daemon-reload
check_result "Systemd daemon reloaded" "Failed to reload systemd daemon"

systemctl enable vpn-api >/dev/null 2>&1
check_result "VPN API service enabled" "Failed to enable VPN API service"

# Test Python script first
print_info "Testing Python script..."
cd /etc/API
python3 -c "import vpn_api" 2>/dev/null
if [ $? -eq 0 ]; then
    print_ok "Python script syntax OK"
else
    print_error "Python script has syntax errors"
    python3 -c "import vpn_api"
    exit 1
fi

# Start VPN API service
print_info "Starting VPN API service..."
systemctl start vpn-api
sleep 5

# Check if services are running with detailed error info
if systemctl is-active --quiet vpn-api; then
    print_ok "VPN API service is running"
else
    print_error "VPN API service failed to start"
    print_info "Service status:"
    systemctl status vpn-api --no-pager -l
    print_info "Recent logs:"
    journalctl -u vpn-api --no-pager -n 10
    
    # Try direct Python execution for debugging
    print_info "Trying direct Python execution..."
    cd /etc/API
    timeout 10s python3 vpn_api.py &
    sleep 3
    if curl -s http://localhost:7777/api/v1/info >/dev/null 2>&1; then
        print_warning "API works with direct Python, issue might be with gunicorn"
        pkill -f vpn_api.py
    fi
    exit 1
fi

# Start/restart Nginx
print_info "Starting Nginx..."
systemctl restart nginx
if systemctl is-active --quiet nginx; then
    print_ok "Nginx service is running"
else
    print_error "Nginx service failed to start"
    nginx -t
    exit 1
fi

# Get server IP
SERVER_IP=$(curl -s ipv4.icanhazip.com 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

# Test API
print_info "Testing API endpoint..."
API_TEST=$(curl -s -H "X-API-Key: $DEFAULT_API_KEY" "http://localhost:7777/api/v1/info" 2>/dev/null)
if echo "$API_TEST" | grep -q "success"; then
    print_ok "API is responding correctly"
else
    print_warning "API test failed, but service is running"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          INSTALLATION COMPLETED         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}API Information:${NC}"
echo -e "API URL: http://$SERVER_IP:7777"
echo -e "API Key: $DEFAULT_API_KEY"
echo ""
echo -e "${CYAN}Management Commands:${NC}"
echo -e "Start service: ${YELLOW}systemctl start vpn-api${NC}"
echo -e "Stop service: ${YELLOW}systemctl stop vpn-api${NC}"
echo -e "Restart service: ${YELLOW}systemctl restart vpn-api${NC}"
echo -e "Check status: ${YELLOW}systemctl status vpn-api${NC}"
echo -e "View logs: ${YELLOW}journalctl -u vpn-api -f${NC}"
echo -e "Management tool: ${YELLOW}vpn-api${NC}"
echo -e "Test API: ${YELLOW}/etc/API/test_api.sh${NC}"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo -e "README: /etc/API/README.md"
echo -e "API Docs: /etc/API/API_DOCUMENTATION.md"
echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"

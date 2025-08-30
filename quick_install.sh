#!/bin/bash

# =========================================
# VPN Management API - One Click Installer
# Quick installer from GitHub raw content
# =========================================

# Script info
SCRIPT_VERSION="1.0"
GITHUB_REPO="alrel1408/API"
GITHUB_RAW="https://raw.githubusercontent.com/$GITHUB_REPO/main"

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fungsi untuk print dengan warna
print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Fungsi untuk cek hasil command
check_result() {
    if [ $? -eq 0 ]; then
        print_ok "$1"
    else
        print_error "$2"
        exit 1
    fi
}

# Banner
clear
echo -e "${PURPLE}╔══════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║          VPN MANAGEMENT API              ║${NC}"
echo -e "${PURPLE}║        ONE CLICK INSTALLER v$SCRIPT_VERSION        ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════╝${NC}"
echo ""
print_info "Installing VPN Management API from GitHub..."
echo ""

# Cek apakah script dijalankan sebagai root
if [[ $EUID -ne 0 ]]; then
   print_error "Script ini harus dijalankan sebagai root!"
   echo "Gunakan: sudo bash <(curl -sL $GITHUB_RAW/quick_install.sh)"
   exit 1
fi

# Cek koneksi internet
print_info "Checking internet connection..."
if ! curl -s --max-time 10 --user-agent "VPN-API-Installer/1.0" https://github.com >/dev/null; then
    print_error "Tidak ada koneksi internet atau GitHub tidak dapat diakses"
    exit 1
fi
print_ok "Internet connection OK"

# Cek sistem operasi
if [[ -f /etc/debian_version ]]; then
    OS="debian"
    print_info "Detected OS: Debian/Ubuntu"
elif [[ -f /etc/redhat-release ]]; then
    OS="centos"
    print_info "Detected OS: CentOS/RHEL"
else
    print_error "Sistem operasi tidak didukung!"
    exit 1
fi

# Update sistem
print_info "Updating system packages..."
if [[ "$OS" == "debian" ]]; then
    apt update >/dev/null 2>&1
    check_result "System packages updated" "Failed to update system packages"
else
    yum update -y >/dev/null 2>&1
    check_result "System packages updated" "Failed to update system packages"
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

# Update pip first
print_info "Updating pip..."
python3 -m pip install --upgrade pip >/dev/null 2>&1

# Try different installation methods
print_info "Installing Flask, Flask-Limiter, and Gunicorn..."

# Method 1: Standard installation
if pip3 install flask flask-limiter gunicorn >/dev/null 2>&1; then
    print_ok "Python packages installed successfully"
# Method 2: With --break-system-packages (for newer Ubuntu/Debian)
elif pip3 install flask flask-limiter gunicorn --break-system-packages >/dev/null 2>&1; then
    print_ok "Python packages installed successfully (system packages)"
# Method 3: Using python3 -m pip
elif python3 -m pip install flask flask-limiter gunicorn >/dev/null 2>&1; then
    print_ok "Python packages installed successfully (python3 -m pip)"
# Method 4: With user agent and timeout
elif pip3 install flask flask-limiter gunicorn --timeout 60 --retries 3 >/dev/null 2>&1; then
    print_ok "Python packages installed successfully (with retry)"
else
    print_error "Failed to install Python packages with all methods"
    print_info "Trying manual installation with verbose output..."
    
    # Show detailed error for debugging
    echo "Attempting manual installation:"
    pip3 install flask flask-limiter gunicorn --verbose
    
    if [ $? -ne 0 ]; then
        print_error "Manual installation also failed"
        print_info "Please check your internet connection and Python installation"
        print_info "You can try manually: sudo pip3 install flask flask-limiter gunicorn"
        exit 1
    fi
fi

# Create directories
print_info "Creating directories..."
mkdir -p /etc/API
mkdir -p /var/log/api
mkdir -p /var/www/html
check_result "Directories created" "Failed to create directories"

# Download main API file
print_info "Downloading VPN API main file..."
if curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/vpn_api.py" -o /etc/API/vpn_api.py; then
    # Verify file was downloaded and is not empty
    if [ -s "/etc/API/vpn_api.py" ] && head -1 /etc/API/vpn_api.py | grep -q "python"; then
        print_ok "API file downloaded successfully"
    else
        print_error "Downloaded file is empty or corrupted"
        print_info "URL: $GITHUB_RAW/vpn_api.py"
        exit 1
    fi
else
    print_error "Failed to download API file from GitHub"
    print_info "URL: $GITHUB_RAW/vpn_api.py"
    print_info "Please check your internet connection and GitHub access"
    exit 1
fi

# Download management scripts
print_info "Downloading management scripts..."
curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/manage_api.sh" -o /etc/API/manage_api.sh
curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/test_api.sh" -o /etc/API/test_api.sh
curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/uninstall_api.sh" -o /etc/API/uninstall_api.sh
check_result "Management scripts downloaded" "Failed to download management scripts"

# Download documentation
print_info "Downloading documentation..."
curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/README.md" -o /etc/API/README.md
curl -sL --retry 3 --retry-delay 2 --user-agent "VPN-API-Installer/1.0" --connect-timeout 30 "$GITHUB_RAW/API_DOCUMENTATION.md" -o /etc/API/API_DOCUMENTATION.md
check_result "Documentation downloaded" "Failed to download documentation"

# Set permissions
chmod +x /etc/API/*.sh
chmod +x /etc/API/vpn_api.py
check_result "Permissions set" "Failed to set permissions"

# Generate default API key
print_info "Generating API configuration..."
DEFAULT_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create API keys file
cat > /etc/API/api_keys.json << EOF
{
  "default": {
    "key": "$DEFAULT_API_KEY",
    "name": "Default Admin",
    "permissions": ["all"],
    "created": "$(date -Iseconds)"
  }
}
EOF
check_result "API keys generated" "Failed to generate API keys"

# Test gunicorn installation
print_info "Testing gunicorn installation..."
if python3 -m gunicorn --version >/dev/null 2>&1; then
    print_ok "Gunicorn is available"
    USE_GUNICORN=true
else
    print_warning "Gunicorn not available, using direct Python execution"
    USE_GUNICORN=false
fi

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
ExecStart=/usr/bin/python3 -m gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 vpn_api:app
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
    listen 5000;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Headers untuk CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-API-Key";
        
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-API-Key";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
}
EOF

# Enable Nginx site
if [[ "$OS" == "debian" ]]; then
    ln -sf /etc/nginx/sites-available/vpn-api /etc/nginx/sites-enabled/
else
    cp /etc/nginx/sites-available/vpn-api /etc/nginx/conf.d/vpn-api.conf
fi

# Test Nginx configuration
nginx -t >/dev/null 2>&1
check_result "Nginx configured" "Nginx configuration failed"

# Create management command
print_info "Creating management command..."
cat > /usr/local/bin/vpn-api << 'EOF'
#!/bin/bash

case "$1" in
    start)
        systemctl start vpn-api
        echo "VPN API started"
        ;;
    stop)
        systemctl stop vpn-api
        echo "VPN API stopped"
        ;;
    restart)
        systemctl restart vpn-api
        echo "VPN API restarted"
        ;;
    status)
        systemctl status vpn-api
        ;;
    logs)
        tail -f /var/log/api/vpn_api.log
        ;;
    key)
        if [ -f "/etc/API/api_keys.json" ]; then
            echo "Current API Keys:"
            cat /etc/API/api_keys.json | python3 -m json.tool
        else
            echo "No API keys found"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|key}"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/vpn-api
check_result "Management command created" "Failed to create management command"

# Configure firewall
print_info "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 5000/tcp >/dev/null 2>&1
    print_ok "UFW rule added for port 5000"
elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=5000/tcp >/dev/null 2>&1
    firewall-cmd --reload >/dev/null 2>&1
    print_ok "Firewalld rule added for port 5000"
else
    print_warning "No supported firewall found, ensure port 5000 is open"
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
    if curl -s http://localhost:5000/api/v1/info >/dev/null 2>&1; then
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
SERVER_IP=$(curl -s --user-agent "VPN-API-Installer/1.0" --max-time 10 ipv4.icanhazip.com 2>/dev/null || curl -s --user-agent "VPN-API-Installer/1.0" --max-time 10 ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

# Test API
print_info "Testing API endpoint..."
API_TEST=$(curl -s --user-agent "VPN-API-Installer/1.0" --max-time 10 -H "X-API-Key: $DEFAULT_API_KEY" "http://localhost:5000/api/v1/info" 2>/dev/null)
if echo "$API_TEST" | grep -q "success"; then
    print_ok "API is responding correctly"
else
    print_warning "API test failed, but service is running"
    print_info "API Response: $API_TEST"
    print_info "You can test manually with: curl -H \"X-API-Key: $DEFAULT_API_KEY\" http://localhost:5000/api/v1/info"
fi

# Save installation info
cat > /root/vpn-api-install.txt << EOF
VPN Management API - Installation Complete
========================================

Installation Date: $(date)
Server IP: $SERVER_IP
API URL: http://$SERVER_IP:5000
API Key: $DEFAULT_API_KEY

Quick Commands:
- vpn-api start/stop/restart/status
- vpn-api logs (view logs)
- vpn-api key (show API keys)

Management:
- /etc/API/manage_api.sh (management panel)
- /etc/API/test_api.sh (test all endpoints)

Files Location:
- API Code: /etc/API/vpn_api.py
- Config: /etc/API/api_keys.json
- Database: /etc/API/vpn_accounts.db
- Logs: /var/log/api/vpn_api.log

Uninstall:
- /etc/API/uninstall_api.sh

GitHub Repository: https://github.com/alrel1408/API
EOF

# Success message
clear
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        INSTALLATION SUCCESSFUL!         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}🎉 VPN Management API berhasil diinstall!${NC}"
echo ""
echo -e "${CYAN}📋 INFORMASI AKSES:${NC}"
echo -e "   🌐 API URL     : ${YELLOW}http://$SERVER_IP:5000${NC}"
echo -e "   🔑 API Key     : ${YELLOW}$DEFAULT_API_KEY${NC}"
echo -e "   📁 Directory   : ${YELLOW}/etc/API/${NC}"
echo ""
echo -e "${CYAN}🛠️  QUICK COMMANDS:${NC}"
echo -e "   ${GREEN}vpn-api start${NC}      - Start service"
echo -e "   ${GREEN}vpn-api stop${NC}       - Stop service"
echo -e "   ${GREEN}vpn-api restart${NC}    - Restart service"
echo -e "   ${GREEN}vpn-api status${NC}     - Check status"
echo -e "   ${GREEN}vpn-api logs${NC}       - View logs"
echo -e "   ${GREEN}vpn-api key${NC}        - Show API keys"
echo ""
echo -e "${CYAN}🔧 MANAGEMENT TOOLS:${NC}"
echo -e "   ${GREEN}/etc/API/manage_api.sh${NC}  - Management panel"
echo -e "   ${GREEN}/etc/API/test_api.sh${NC}    - Test all endpoints"
echo ""
echo -e "${CYAN}📚 CONTOH PENGGUNAAN:${NC}"
echo -e "   # Test API"
echo -e "   ${YELLOW}curl -H \"X-API-Key: $DEFAULT_API_KEY\" http://$SERVER_IP:5000/api/v1/info${NC}"
echo ""
echo -e "   # Buat SSH trial"
echo -e "   ${YELLOW}curl -X POST -H \"X-API-Key: $DEFAULT_API_KEY\" http://$SERVER_IP:5000/api/v1/trial/ssh${NC}"
echo ""
echo -e "${CYAN}📖 DOKUMENTASI:${NC}"
echo -e "   ${GREEN}/etc/API/README.md${NC}              - Quick guide"
echo -e "   ${GREEN}/etc/API/API_DOCUMENTATION.md${NC}   - Full documentation"
echo ""
echo -e "${CYAN}🗑️  UNINSTALL:${NC}"
echo -e "   ${RED}/etc/API/uninstall_api.sh${NC}        - Remove API completely"
echo ""
print_ok "Installation info saved to: /root/vpn-api-install.txt"
echo ""
echo -e "${GREEN}✨ API siap digunakan! Happy coding! 🚀${NC}"
echo ""

# Cleanup
rm -f /tmp/vpn-api-install.log 2>/dev/null

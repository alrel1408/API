#!/bin/bash

# =========================================
# Quick VPN API Test Script  
# Untuk debugging masalah API
# =========================================

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🔍 VPN API Quick Diagnostic"
echo "=========================="
echo ""

# 1. Check service status
print_info "Checking VPN API service status..."
if systemctl is-active --quiet vpn-api; then
    print_ok "VPN API service is running"
    systemctl status vpn-api --no-pager -l
else
    print_error "VPN API service is NOT running"
    print_info "Trying to start service..."
    systemctl start vpn-api
    sleep 3
    if systemctl is-active --quiet vpn-api; then
        print_ok "Service started successfully"
    else
        print_error "Failed to start service"
        print_info "Checking logs..."
        journalctl -u vpn-api --no-pager -l -n 20
        exit 1
    fi
fi
echo ""

# 2. Check listening ports
print_info "Checking listening ports..."
echo "Ports that API might be using:"
netstat -tlnp 2>/dev/null | grep -E ":(5000|7000|7777)" || echo "No API ports found listening"
echo ""

# 3. Check API key file
print_info "Checking API key file..."
API_KEY_FILE="/etc/API/api_keys.json"
if [ -f "$API_KEY_FILE" ]; then
    print_ok "API key file exists"
    echo "File content:"
    cat "$API_KEY_FILE"
    echo ""
    
    # Extract API key
    API_KEY=$(python3 -c "
import json
try:
    with open('$API_KEY_FILE', 'r') as f:
        data = json.load(f)
        if 'keys' in data and isinstance(data['keys'], list) and len(data['keys']) > 0:
            print(data['keys'][0]['key'])
        elif 'default' in data and 'key' in data['default']:
            print(data['default']['key'])
        elif 'key' in data:
            print(data['key'])
        else:
            print('')
except:
    print('')
" 2>/dev/null)
    
    if [ -n "$API_KEY" ]; then
        print_ok "API key extracted: ${API_KEY:0:8}..."
    else
        print_error "Failed to extract API key"
    fi
else
    print_error "API key file not found: $API_KEY_FILE"
fi
echo ""

# 4. Test API endpoints
if [ -n "$API_KEY" ]; then
    print_info "Testing API endpoints..."
    
    # Try different ports
    for PORT in 5000 7000 7777; do
        echo "Testing port $PORT..."
        
        response=$(curl -s -w "HTTP_CODE:%{http_code}" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            --connect-timeout 5 \
            "http://localhost:$PORT/api/v1/info" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
            response_body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
            
            if [ "$http_code" = "200" ]; then
                print_ok "Port $PORT: Working! Response: $http_code"
                echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
                WORKING_PORT=$PORT
                break
            else
                print_warning "Port $PORT: HTTP $http_code"
                echo "$response_body"
            fi
        else
            print_warning "Port $PORT: Connection failed"
        fi
        echo ""
    done
    
    if [ -n "$WORKING_PORT" ]; then
        print_ok "API is working on port $WORKING_PORT"
        echo ""
        print_info "You can now test with:"
        echo "curl -H \"X-API-Key: $API_KEY\" http://localhost:$WORKING_PORT/api/v1/info"
    else
        print_error "API is not responding on any expected port"
    fi
else
    print_error "Cannot test API endpoints without valid API key"
fi

echo ""
print_info "Diagnostic complete!"

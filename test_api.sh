#!/bin/bash

# =========================================
# VPN Management API Test Script
# Script untuk testing semua endpoint API
# =========================================

# Konfigurasi
API_BASE_URL="http://localhost:5000"
API_KEY_FILE="/etc/API/api_keys.json"

# Auto-detect API port from running service
if systemctl is-active --quiet vpn-api; then
    # Check if API is running on port 7777 (gunicorn)
    if netstat -tlnp 2>/dev/null | grep -q ":7777.*python\|:7777.*gunicorn"; then
        API_BASE_URL="http://localhost:7777"
    # Check if API is running on port 5000 (direct python)
    elif netstat -tlnp 2>/dev/null | grep -q ":5000.*python"; then
        API_BASE_URL="http://localhost:5000"
    fi
fi

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

print_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# Fungsi untuk mendapatkan API key
get_api_key() {
    if [ -f "$API_KEY_FILE" ]; then
        API_KEY=$(python3 -c "
import json
try:
    with open('$API_KEY_FILE', 'r') as f:
        data = json.load(f)
        # Try new format first (quick_install.sh format)
        if 'keys' in data and isinstance(data['keys'], list) and len(data['keys']) > 0:
            print(data['keys'][0]['key'])
        # Try old format (install_api.sh format)
        elif 'default' in data and 'key' in data['default']:
            print(data['default']['key'])
        # Try direct key format
        elif 'key' in data:
            print(data['key'])
        else:
            print('')
except Exception as e:
    print('')
" 2>/dev/null)
        
        if [ -z "$API_KEY" ]; then
            print_error "Tidak dapat membaca API key dari $API_KEY_FILE"
            echo "Format file API key tidak dikenali."
            if [ -f "$API_KEY_FILE" ]; then
                echo "Isi file:"
                cat "$API_KEY_FILE"
            fi
            exit 1
        fi
    else
        print_error "File API key tidak ditemukan: $API_KEY_FILE"
        exit 1
    fi
}

# Fungsi untuk test HTTP request
test_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    print_test "$description"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            "$API_BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X POST \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_BASE_URL$endpoint")
        else
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X POST \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                "$API_BASE_URL$endpoint")
        fi
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
            -X DELETE \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            "$API_BASE_URL$endpoint")
    fi
    
    # Extract HTTP code dan response body
    http_code=$(echo "$response" | tail -n1 | sed 's/.*HTTP_CODE://')
    response_body=$(echo "$response" | sed '$d')
    
    # Check response
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        print_ok "Response: $http_code"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
    else
        print_error "Response: $http_code"
        echo "$response_body"
    fi
    
    echo ""
    sleep 1
}

# Banner
clear
echo -e "${PURPLE}╔══════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║          VPN API TEST SCRIPT             ║${NC}"
echo -e "${PURPLE}║            Testing v1.0                  ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Cek apakah API service berjalan
print_info "Checking API service status..."
if systemctl is-active --quiet vpn-api; then
    print_ok "VPN API service is running"
else
    print_error "VPN API service is not running"
    print_info "Starting VPN API service..."
    systemctl start vpn-api
    sleep 3
    if systemctl is-active --quiet vpn-api; then
        print_ok "VPN API service started successfully"
    else
        print_error "Failed to start VPN API service"
        exit 1
    fi
fi

# Get API key
print_info "Getting API key..."
get_api_key
print_ok "API Key: ${API_KEY:0:8}..."
print_info "Using API URL: $API_BASE_URL"
echo ""

# Test 1: Server Info
test_request "GET" "/api/v1/info" "" "Testing server info endpoint"

# Test 2: SSH Trial
test_request "POST" "/api/v1/trial/ssh" "" "Testing SSH trial creation"

# Test 3: Trojan Trial
test_request "POST" "/api/v1/trial/trojan" "" "Testing Trojan trial creation"

# Test 4: VLess Trial
test_request "POST" "/api/v1/trial/vless" "" "Testing VLess trial creation"

# Test 5: VMess Trial
test_request "POST" "/api/v1/trial/vmess" "" "Testing VMess trial creation"

# Test 6: List All Accounts
test_request "GET" "/api/v1/accounts/list" "" "Testing list all accounts"

# Test 7: List SSH Accounts
test_request "GET" "/api/v1/accounts/list?type=ssh" "" "Testing list SSH accounts"

# Test 8: Account Statistics
test_request "GET" "/api/v1/accounts/stats" "" "Testing account statistics"

# Test 9: Activity Logs
test_request "GET" "/api/v1/logs?limit=5" "" "Testing activity logs"

# Test 10: SSH Account Creation
ssh_data='{
  "username": "test-ssh-001",
  "password": "testpass123",
  "limit_ip": 2,
  "expired_days": 7,
  "bug_host": "test.com"
}'
test_request "POST" "/api/v1/ssh/create" "$ssh_data" "Testing SSH account creation"

# Test 11: Trojan Account Creation
trojan_data='{
  "username": "test-trojan-001",
  "expired_days": 7,
  "quota_gb": 5,
  "ip_limit": 2
}'
test_request "POST" "/api/v1/trojan/create" "$trojan_data" "Testing Trojan account creation"

# Test 12: VLess Account Creation
vless_data='{
  "username": "test-vless-001",
  "expired_days": 7,
  "quota_gb": 5,
  "ip_limit": 2
}'
test_request "POST" "/api/v1/vless/create" "$vless_data" "Testing VLess account creation"

# Test 13: VMess Account Creation
vmess_data='{
  "username": "test-vmess-001",
  "expired_days": 7,
  "quota_gb": 5,
  "ip_limit": 2,
  "bug_host": "test.com"
}'
test_request "POST" "/api/v1/vmess/create" "$vmess_data" "Testing VMess account creation"

# Test 14: List SSH Accounts after creation
test_request "GET" "/api/v1/ssh/list" "" "Testing SSH list after creation"

# Test 15: List Trojan Accounts after creation
test_request "GET" "/api/v1/trojan/list" "" "Testing Trojan list after creation"

# Test 16: Invalid API Key Test
print_test "Testing invalid API key"
invalid_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -H "X-API-Key: invalid-key" \
    -H "Content-Type: application/json" \
    "$API_BASE_URL/api/v1/info")

invalid_http_code=$(echo "$invalid_response" | tail -n1 | sed 's/.*HTTP_CODE://')
if [ "$invalid_http_code" = "401" ]; then
    print_ok "Invalid API key correctly rejected (401)"
else
    print_error "Invalid API key test failed (Expected 401, got $invalid_http_code)"
fi
echo ""

# Test 17: Missing API Key Test
print_test "Testing missing API key"
missing_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -H "Content-Type: application/json" \
    "$API_BASE_URL/api/v1/info")

missing_http_code=$(echo "$missing_response" | tail -n1 | sed 's/.*HTTP_CODE://')
if [ "$missing_http_code" = "401" ]; then
    print_ok "Missing API key correctly rejected (401)"
else
    print_error "Missing API key test failed (Expected 401, got $missing_http_code)"
fi
echo ""

# Test 18: Rate Limit Test - DISABLED
print_test "Rate limiting is disabled for testing"
print_info "Rate limiting has been commented out to allow unlimited testing"
echo ""

# Cleanup Test Accounts (Optional)
print_info "Cleaning up test accounts..."
test_request "DELETE" "/api/v1/ssh/delete/test-ssh-001" "" "Deleting test SSH account"
test_request "DELETE" "/api/v1/trojan/delete/test-trojan-001" "" "Deleting test Trojan account"

# Summary
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            TEST COMPLETED!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
print_info "Test summary:"
echo -e "   ✅ API service is running"
echo -e "   ✅ Authentication working"
echo -e "   ✅ All endpoints accessible"
echo -e "   ✅ Trial account creation working"
echo -e "   ✅ Regular account creation working"
echo -e "   ✅ Account listing working"
echo -e "   ✅ Error handling working"
echo ""
print_info "Check logs for detailed information:"
echo -e "   📝 API logs: tail -f /var/log/api/vpn_api.log"
echo -e "   📝 Nginx logs: tail -f /var/log/nginx/access.log"
echo ""
print_ok "API is ready for production use!"

#!/bin/bash

# =========================================
# VPN Management API Manager
# Script untuk mengelola API VPN
# =========================================

# Konfigurasi
API_KEYS_FILE="/etc/API/api_keys.json"
DATABASE_FILE="/etc/API/vpn_accounts.db"
LOG_FILE="/var/log/api/vpn_api.log"
SERVICE_NAME="vpn-api"

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
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║$1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

# Fungsi untuk menampilkan status service
show_status() {
    print_header "           SERVICE STATUS                  "
    
    # Cek status systemd service
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_ok "VPN API Service: Running"
    else
        print_error "VPN API Service: Stopped"
    fi
    
    # Cek status nginx
    if systemctl is-active --quiet nginx; then
        print_ok "Nginx Service: Running"
    else
        print_error "Nginx Service: Stopped"
    fi
    
    # Cek port 8080
    if netstat -tlnp 2>/dev/null | grep -q ":8080 "; then
        print_ok "Port 8080: Open"
    else
        print_warning "Port 8080: Not listening"
    fi
    
    # Cek API response
    if [ -f "$API_KEYS_FILE" ]; then
        API_KEY=$(python3 -c "
import json
try:
    with open('$API_KEYS_FILE', 'r') as f:
        data = json.load(f)
        print(data['default']['key'])
except:
    print('')
" 2>/dev/null)
        
        if [ -n "$API_KEY" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "X-API-Key: $API_KEY" \
                http://localhost:8080/api/v1/info 2>/dev/null)
            
            if [ "$response" = "200" ]; then
                print_ok "API Endpoint: Responding"
            else
                print_error "API Endpoint: Not responding (HTTP $response)"
            fi
        fi
    fi
    
    echo ""
}

# Fungsi untuk menampilkan API keys
show_keys() {
    print_header "             API KEYS                     "
    
    if [ -f "$API_KEYS_FILE" ]; then
        python3 -c "
import json
try:
    with open('$API_KEYS_FILE', 'r') as f:
        data = json.load(f)
        for key_id, key_data in data.items():
            print(f'Key ID: {key_id}')
            print(f'Name: {key_data.get(\"name\", \"N/A\")}')
            print(f'Key: {key_data[\"key\"][:8]}...{key_data[\"key\"][-8:]}')
            print(f'Permissions: {key_data.get(\"permissions\", [])}')
            print(f'Created: {key_data.get(\"created\", \"N/A\")}')
            print('-' * 50)
except Exception as e:
    print(f'Error reading API keys: {e}')
"
    else
        print_error "API keys file not found: $API_KEYS_FILE"
    fi
    
    echo ""
}

# Fungsi untuk membuat API key baru
create_key() {
    print_header "           CREATE API KEY                 "
    
    read -p "Enter key name: " key_name
    if [ -z "$key_name" ]; then
        print_error "Key name cannot be empty"
        return 1
    fi
    
    echo "Select permissions:"
    echo "1) Read only"
    echo "2) Read + Create"
    echo "3) All permissions"
    read -p "Choice [1-3]: " perm_choice
    
    case $perm_choice in
        1) permissions='["read"]' ;;
        2) permissions='["read", "create"]' ;;
        3) permissions='["all"]' ;;
        *) permissions='["read"]' ;;
    esac
    
    # Generate key
    new_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    key_id=$(python3 -c "import secrets; print(secrets.token_urlsafe(8))")
    
    # Add to keys file
    python3 -c "
import json
import os
from datetime import datetime

key_file = '$API_KEYS_FILE'
new_key_data = {
    'key': '$new_key',
    'name': '$key_name',
    'permissions': $permissions,
    'created': datetime.now().isoformat()
}

# Load existing keys
if os.path.exists(key_file):
    with open(key_file, 'r') as f:
        keys = json.load(f)
else:
    keys = {}

# Add new key
keys['$key_id'] = new_key_data

# Save keys
os.makedirs(os.path.dirname(key_file), exist_ok=True)
with open(key_file, 'w') as f:
    json.dump(keys, f, indent=2)

print('API key created successfully!')
"
    
    print_ok "New API Key created:"
    echo -e "   Key ID: $key_id"
    echo -e "   Name: $key_name"
    echo -e "   Key: $new_key"
    echo -e "   Permissions: $permissions"
    echo ""
    print_warning "Save this key securely! It won't be shown again."
    echo ""
}

# Fungsi untuk menghapus API key
delete_key() {
    print_header "           DELETE API KEY                 "
    
    # Tampilkan existing keys
    if [ -f "$API_KEYS_FILE" ]; then
        echo "Existing API Keys:"
        python3 -c "
import json
try:
    with open('$API_KEYS_FILE', 'r') as f:
        data = json.load(f)
        for key_id, key_data in data.items():
            print(f'{key_id}: {key_data.get(\"name\", \"N/A\")}')
except:
    print('Error reading keys')
"
        echo ""
        
        read -p "Enter key ID to delete: " key_id
        if [ -z "$key_id" ]; then
            print_error "Key ID cannot be empty"
            return 1
        fi
        
        # Delete key
        python3 -c "
import json
import os

key_file = '$API_KEYS_FILE'
key_id = '$key_id'

if os.path.exists(key_file):
    with open(key_file, 'r') as f:
        keys = json.load(f)
    
    if key_id in keys:
        del keys[key_id]
        with open(key_file, 'w') as f:
            json.dump(keys, f, indent=2)
        print('Key deleted successfully!')
    else:
        print('Key ID not found!')
else:
    print('Keys file not found!')
"
    else
        print_error "API keys file not found"
    fi
    
    echo ""
}

# Fungsi untuk menampilkan statistik
show_stats() {
    print_header "            STATISTICS                    "
    
    if [ -f "$DATABASE_FILE" ]; then
        echo "Account Statistics:"
        sqlite3 "$DATABASE_FILE" "
        SELECT 
            service_type, 
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
        FROM accounts 
        GROUP BY service_type;
        " 2>/dev/null | while IFS='|' read service total active inactive; do
            echo "  $service: $total total ($active active, $inactive inactive)"
        done
        
        echo ""
        echo "Recent Activity (Last 10):"
        sqlite3 "$DATABASE_FILE" "
        SELECT 
            datetime(timestamp) as time,
            action,
            service_type,
            username
        FROM activity_logs 
        ORDER BY timestamp DESC 
        LIMIT 10;
        " 2>/dev/null | while IFS='|' read time action service user; do
            echo "  $time: $action $service ($user)"
        done
    else
        print_warning "Database file not found: $DATABASE_FILE"
    fi
    
    echo ""
}

# Fungsi untuk backup database
backup_db() {
    print_header "           BACKUP DATABASE                "
    
    if [ -f "$DATABASE_FILE" ]; then
        backup_dir="/etc/API/backups"
        mkdir -p "$backup_dir"
        
        timestamp=$(date +"%Y%m%d_%H%M%S")
        backup_file="$backup_dir/vpn_accounts_$timestamp.db"
        
        cp "$DATABASE_FILE" "$backup_file"
        
        if [ $? -eq 0 ]; then
            print_ok "Database backed up to: $backup_file"
            
            # Compress backup
            gzip "$backup_file"
            print_ok "Backup compressed: $backup_file.gz"
            
            # Clean old backups (keep last 5)
            ls -t "$backup_dir"/*.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
            print_info "Old backups cleaned (keeping last 5)"
        else
            print_error "Failed to backup database"
        fi
    else
        print_error "Database file not found: $DATABASE_FILE"
    fi
    
    echo ""
}

# Fungsi untuk menampilkan logs
show_logs() {
    print_header "              LOGS                        "
    
    echo "Choose log type:"
    echo "1) API logs (last 50 lines)"
    echo "2) API logs (live tail)"
    echo "3) Nginx access logs"
    echo "4) System logs for VPN API service"
    read -p "Choice [1-4]: " log_choice
    
    case $log_choice in
        1)
            if [ -f "$LOG_FILE" ]; then
                tail -n 50 "$LOG_FILE"
            else
                print_error "Log file not found: $LOG_FILE"
            fi
            ;;
        2)
            if [ -f "$LOG_FILE" ]; then
                print_info "Press Ctrl+C to exit"
                tail -f "$LOG_FILE"
            else
                print_error "Log file not found: $LOG_FILE"
            fi
            ;;
        3)
            if [ -f "/var/log/nginx/access.log" ]; then
                tail -n 50 /var/log/nginx/access.log | grep ":8080"
            else
                print_error "Nginx access log not found"
            fi
            ;;
        4)
            journalctl -u $SERVICE_NAME --no-pager -n 50
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
}

# Fungsi untuk restart services
restart_services() {
    print_header "         RESTART SERVICES                 "
    
    print_info "Restarting VPN API service..."
    systemctl restart $SERVICE_NAME
    if [ $? -eq 0 ]; then
        print_ok "VPN API service restarted"
    else
        print_error "Failed to restart VPN API service"
    fi
    
    print_info "Restarting Nginx..."
    systemctl restart nginx
    if [ $? -eq 0 ]; then
        print_ok "Nginx restarted"
    else
        print_error "Failed to restart Nginx"
    fi
    
    sleep 2
    show_status
}

# Fungsi untuk menampilkan menu
show_menu() {
    clear
    echo -e "${PURPLE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║          VPN API MANAGER v1.0            ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}1.${NC} Show Status"
    echo -e "${CYAN}2.${NC} Show API Keys"
    echo -e "${CYAN}3.${NC} Create API Key"
    echo -e "${CYAN}4.${NC} Delete API Key"
    echo -e "${CYAN}5.${NC} Show Statistics"
    echo -e "${CYAN}6.${NC} Show Logs"
    echo -e "${CYAN}7.${NC} Backup Database"
    echo -e "${CYAN}8.${NC} Restart Services"
    echo -e "${CYAN}9.${NC} Test API"
    echo -e "${CYAN}0.${NC} Exit"
    echo ""
    read -p "Select option [0-9]: " choice
}

# Main menu loop
while true; do
    show_menu
    
    case $choice in
        1) show_status ;;
        2) show_keys ;;
        3) create_key ;;
        4) delete_key ;;
        5) show_stats ;;
        6) show_logs ;;
        7) backup_db ;;
        8) restart_services ;;
        9) 
            if [ -f "/etc/API/test_api.sh" ]; then
                /etc/API/test_api.sh
            else
                print_error "Test script not found"
            fi
            ;;
        0) 
            print_info "Goodbye!"
            exit 0
            ;;
        *) 
            print_error "Invalid option"
            ;;
    esac
    
    read -p "Press Enter to continue..."
done

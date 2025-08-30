#!/bin/bash

# =========================================
# VPN Management API Uninstaller
# Script untuk menghapus VPN Management API
# =========================================

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

print_question() {
    echo -e "${CYAN}[QUESTION]${NC} $1"
}

# Fungsi untuk konfirmasi
confirm() {
    while true; do
        read -p "$1 [y/N]: " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Banner
clear
echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
echo -e "${RED}║        VPN MANAGEMENT API                ║${NC}"
echo -e "${RED}║            UNINSTALLER                   ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
echo ""

# Cek apakah script dijalankan sebagai root
if [[ $EUID -ne 0 ]]; then
   print_error "Script ini harus dijalankan sebagai root!"
   exit 1
fi

# Warning dan konfirmasi
print_warning "PERINGATAN: Script ini akan menghapus semua komponen VPN Management API!"
echo ""
echo -e "${YELLOW}Komponen yang akan dihapus:${NC}"
echo "  • VPN API Service (vpn-api)"
echo "  • Nginx configuration"
echo "  • API files di /etc/API/"
echo "  • Log files di /var/log/api/"
echo "  • Management command di /usr/local/bin/vpn-api"
echo "  • Systemd service file"
echo "  • Python packages (opsional)"
echo ""

if ! confirm "Apakah Anda yakin ingin melanjutkan uninstall?"; then
    print_info "Uninstall dibatalkan."
    exit 0
fi

echo ""

# Backup option
if confirm "Apakah Anda ingin backup database sebelum uninstall?"; then
    BACKUP_DIR="/root/vpn-api-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "/etc/API/vpn_accounts.db" ]; then
        cp "/etc/API/vpn_accounts.db" "$BACKUP_DIR/"
        print_ok "Database backed up to: $BACKUP_DIR/vpn_accounts.db"
    fi
    
    if [ -f "/etc/API/api_keys.json" ]; then
        cp "/etc/API/api_keys.json" "$BACKUP_DIR/"
        print_ok "API keys backed up to: $BACKUP_DIR/api_keys.json"
    fi
    
    if [ -d "/var/log/api" ]; then
        cp -r "/var/log/api" "$BACKUP_DIR/"
        print_ok "Logs backed up to: $BACKUP_DIR/api/"
    fi
    
    echo "Backup completed at: $BACKUP_DIR"
    echo ""
fi

# 1. Stop services
print_info "Stopping services..."
if systemctl is-active --quiet vpn-api; then
    systemctl stop vpn-api
    print_ok "VPN API service stopped"
else
    print_info "VPN API service was not running"
fi

# 2. Disable and remove systemd service
print_info "Removing systemd service..."
if [ -f "/etc/systemd/system/vpn-api.service" ]; then
    systemctl disable vpn-api 2>/dev/null
    rm -f "/etc/systemd/system/vpn-api.service"
    systemctl daemon-reload
    print_ok "Systemd service removed"
else
    print_info "Systemd service file not found"
fi

# 3. Remove Nginx configuration
print_info "Removing Nginx configuration..."
nginx_removed=false

# For Debian/Ubuntu
if [ -L "/etc/nginx/sites-enabled/vpn-api" ]; then
    rm -f "/etc/nginx/sites-enabled/vpn-api"
    print_ok "Nginx symlink removed"
    nginx_removed=true
fi

if [ -f "/etc/nginx/sites-available/vpn-api" ]; then
    rm -f "/etc/nginx/sites-available/vpn-api"
    print_ok "Nginx site configuration removed"
    nginx_removed=true
fi

# For CentOS/RHEL
if [ -f "/etc/nginx/conf.d/vpn-api.conf" ]; then
    rm -f "/etc/nginx/conf.d/vpn-api.conf"
    print_ok "Nginx configuration removed"
    nginx_removed=true
fi

if [ "$nginx_removed" = true ]; then
    # Test nginx config and reload if valid
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        print_ok "Nginx reloaded"
    else
        print_warning "Nginx configuration test failed, please check manually"
    fi
else
    print_info "Nginx configuration not found"
fi

# 4. Remove management command
print_info "Removing management command..."
if [ -f "/usr/local/bin/vpn-api" ]; then
    rm -f "/usr/local/bin/vpn-api"
    print_ok "Management command removed"
else
    print_info "Management command not found"
fi

# 5. Remove log directory
print_info "Removing log files..."
if [ -d "/var/log/api" ]; then
    rm -rf "/var/log/api"
    print_ok "Log directory removed"
else
    print_info "Log directory not found"
fi

# 6. Remove API directory
print_info "Removing API files..."
api_dir_removed=false

if confirm "Hapus semua file API di /etc/API/?"; then
    if [ -d "/etc/API" ]; then
        # Show what will be deleted
        echo "Files to be deleted:"
        ls -la /etc/API/ 2>/dev/null | head -20
        echo ""
        
        if confirm "Konfirmasi hapus direktori /etc/API/ dan semua isinya?"; then
            rm -rf "/etc/API"
            print_ok "API directory removed"
            api_dir_removed=true
        else
            print_info "API directory kept"
        fi
    else
        print_info "API directory not found"
    fi
else
    print_info "API directory kept"
fi

# 7. Remove config files generated by API (optional)
if confirm "Hapus file konfigurasi yang dibuat oleh API di /var/www/html/?"; then
    print_info "Removing generated config files..."
    removed_count=0
    
    for pattern in "ssh-*.txt" "trojan-*.txt" "vless-*.txt" "vmess-*.txt"; do
        for file in /var/www/html/$pattern; do
            if [ -f "$file" ]; then
                rm -f "$file"
                ((removed_count++))
            fi
        done
    done
    
    if [ $removed_count -gt 0 ]; then
        print_ok "Removed $removed_count config files from /var/www/html/"
    else
        print_info "No config files found in /var/www/html/"
    fi
fi

# 8. Remove Python packages (optional)
if confirm "Hapus Python packages yang diinstall untuk API (flask, flask-limiter, gunicorn)?"; then
    print_info "Removing Python packages..."
    pip3 uninstall -y flask flask-limiter gunicorn 2>/dev/null
    print_ok "Python packages removed"
fi

# 9. Remove firewall rules (optional)
if confirm "Hapus firewall rule untuk port 5000?"; then
    print_info "Removing firewall rules..."
    
    if command -v ufw >/dev/null 2>&1; then
        ufw delete allow 5000/tcp 2>/dev/null
        print_ok "UFW rule removed for port 5000"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --permanent --remove-port=5000/tcp 2>/dev/null
        firewall-cmd --reload 2>/dev/null
        print_ok "Firewalld rule removed for port 5000"
    else
        print_info "No supported firewall found"
    fi
fi

# 10. Clean up processes
print_info "Cleaning up any remaining processes..."
pkill -f "vpn_api.py" 2>/dev/null || true
pkill -f "python.*vpn_api" 2>/dev/null || true

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           UNINSTALL COMPLETED!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

print_info "Uninstall summary:"
echo "  ✅ VPN API service stopped and disabled"
echo "  ✅ Systemd service file removed"
echo "  ✅ Nginx configuration removed"
echo "  ✅ Management command removed"
echo "  ✅ Log files removed"

if [ "$api_dir_removed" = true ]; then
    echo "  ✅ API directory removed"
else
    echo "  ⚠️  API directory kept (manual removal required)"
fi

echo ""

# Show what's left (if any)
if [ -d "/etc/API" ]; then
    print_warning "Remaining files in /etc/API/:"
    ls -la /etc/API/ 2>/dev/null | head -10
    echo ""
fi

if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
    print_info "Backup tersimpan di: $BACKUP_DIR"
fi

print_info "VPN script asli (SSH, Trojan, VLess, VMess) tetap utuh"
print_info "Database VPN asli (/etc/ssh/, /etc/trojan/, dll) tidak tersentuh"

echo ""

# Final check
remaining_processes=$(pgrep -f "vpn_api" 2>/dev/null | wc -l)
if [ "$remaining_processes" -gt 0 ]; then
    print_warning "Masih ada $remaining_processes proses yang berjalan terkait vpn_api"
    print_info "Jalankan: pkill -f vpn_api untuk menghentikan paksa"
fi

# Port check
if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
    print_warning "Port 5000 masih digunakan oleh proses lain"
    print_info "Cek dengan: netstat -tlnp | grep :5000"
fi

echo ""
print_ok "VPN Management API telah berhasil diuninstall!"
print_info "Terima kasih telah menggunakan VPN Management API"
echo ""

# Self destruct option
if [ "$api_dir_removed" = true ]; then
    if confirm "Hapus script uninstaller ini juga?"; then
        rm -f "$0"
        print_ok "Uninstaller script removed"
    fi
fi

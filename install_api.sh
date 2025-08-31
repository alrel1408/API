#!/bin/bash
#
# =========================================
# VPN Management API Installer
# Auto installer untuk API VPN Management
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

# Fungsi untuk cek apakah command berhasil
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
echo -e "${PURPLE}║            INSTALLER v1.0                ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Cek apakah script dijalankan sebagai root
if [[ $EUID -ne 0 ]]; then
   print_error "Script ini harus dijalankan sebagai root!"
   exit 1
fi

print_info "Memulai instalasi VPN Management API..."

# Cek sistem operasi
if [[ -f /etc/debian_version ]]; then
    OS="debian"
    print_info "Sistem operasi: Debian/Ubuntu"
elif [[ -f /etc/redhat-release ]]; then
    OS="centos"
    print_info "Sistem operasi: CentOS/RHEL"
else
    print_error "Sistem operasi tidak didukung!"
    exit 1
fi

# Update sistem
print_info "Mengupdate sistem..."
if [[ "$OS" == "debian" ]]; then
    apt update && apt upgrade -y
    check_result "Sistem berhasil diupdate" "Gagal mengupdate sistem"
else
    yum update -y
    check_result "Sistem berhasil diupdate" "Gagal mengupdate sistem"
fi

# Install dependencies
print_info "Menginstall dependencies..."

# Cek apakah Nginx sudah terinstall dari Xray setup
if command -v nginx >/dev/null 2>&1; then
    print_warning "Nginx sudah terinstall, melewati instalasi ulang"
    NGINX_INSTALLED=true
else
    NGINX_INSTALLED=false
fi

if [[ "$OS" == "debian" ]]; then
    if [ "$NGINX_INSTALLED" = false ]; then
        apt install -y python3 python3-pip python3-venv nginx supervisor curl wget git
    else
        apt install -y python3 python3-pip python3-venv supervisor curl wget git
    fi
    check_result "Dependencies berhasil diinstall" "Gagal menginstall dependencies"
else
    if [ "$NGINX_INSTALLED" = false ]; then
        yum install -y python3 python3-pip nginx supervisor curl wget git
    else
        yum install -y python3 python3-pip supervisor curl wget git
    fi
    check_result "Dependencies berhasil diinstall" "Gagal menginstall dependencies"
fi

# Buat direktori API
print_info "Membuat direktori API..."
mkdir -p /etc/API
mkdir -p /var/log/api
mkdir -p /var/www/html
check_result "Direktori API berhasil dibuat" "Gagal membuat direktori API"

# Install Python packages
print_info "Menginstall Python packages..."
pip3 install flask flask-limiter gunicorn
check_result "Python packages berhasil diinstall" "Gagal menginstall Python packages"

# Test gunicorn installation
print_info "Testing gunicorn installation..."
if python3 -m gunicorn --version >/dev/null 2>&1; then
    print_ok "Gunicorn is available"
    USE_GUNICORN=true
else
    print_warning "Gunicorn not available, using direct Python execution"
    USE_GUNICORN=false
fi

# Download API files jika belum ada
if [ ! -f "/etc/API/vpn_api.py" ]; then
    print_info "Mendownload file API..."
    
    # Buat file API
    cat > /etc/API/vpn_api.py << 'EOF'
#!/usr/bin/env python3
"""
VPN Management API
API untuk mengelola akun SSH, Trojan, VLess, dan VMess
"""

from flask import Flask, request, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import subprocess
import json
import os
import re
import uuid
import datetime
import hashlib
import hmac
import secrets
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import random

app = Flask(__name__)

# Konfigurasi
API_KEYS_FILE = '/etc/API/api_keys.json'
DATABASE_FILE = '/etc/API/vpn_accounts.db'
LOG_FILE = '/var/log/api/vpn_api.log'

# Setup logging
os.makedirs('/var/log/api', exist_ok=True)
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=10000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Rate limiting - DISABLED FOR TESTING
# limiter = Limiter(
#     app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )

class VPNManager:
    def __init__(self):
        self.init_database()
        self.load_api_keys()
    
    def init_database(self):
        """Inisialisasi database SQLite"""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Tabel untuk menyimpan akun
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT,
                uuid TEXT,
                service_type TEXT NOT NULL,
                quota_gb INTEGER DEFAULT 0,
                ip_limit INTEGER DEFAULT 1,
                created_date TEXT NOT NULL,
                expire_date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                bug_host TEXT DEFAULT 'bug.com'
            )
        ''')
        
        # Tabel untuk log aktivitas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT NOT NULL,
                service_type TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_api_keys(self):
        """Load API keys dari file"""
        try:
            with open(API_KEYS_FILE, 'r') as f:
                self.api_keys = json.load(f)
        except FileNotFoundError:
            # Generate default API key jika file tidak ada
            default_key = secrets.token_urlsafe(32)
            self.api_keys = {
                "default": {
                    "key": default_key,
                    "name": "Default Admin",
                    "permissions": ["all"],
                    "created": datetime.datetime.now().isoformat()
                }
            }
            self.save_api_keys()
            print(f"Default API Key: {default_key}")
    
    def save_api_keys(self):
        """Simpan API keys ke file"""
        os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(self.api_keys, f, indent=2)
    
    def verify_api_key(self, api_key):
        """Verifikasi API key"""
        for key_id, key_data in self.api_keys.items():
            if key_data['key'] == api_key:
                return True, key_data
        return False, None
    
    def log_activity(self, username, action, service_type, ip_address, details=""):
        """Log aktivitas ke database"""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs (username, action, service_type, timestamp, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, action, service_type, datetime.datetime.now().isoformat(), ip_address, details))
        conn.commit()
        conn.close()
    
    def get_server_info(self):
        """Ambil informasi server"""
        try:
            domain = subprocess.check_output(['cat', '/etc/xray/domain'], text=True).strip()
        except:
            domain = 'your-domain.com'
        
        try:
            city = subprocess.check_output(['cat', '/etc/xray/city'], text=True).strip()
        except:
            city = 'Unknown'
        
        try:
            ns_domain = subprocess.check_output(['cat', '/root/nsdomain'], text=True).strip()
        except:
            ns_domain = domain
        
        try:
            pub_key = subprocess.check_output(['cat', '/etc/slowdns/server.pub'], text=True).strip()
        except:
            pub_key = ''
        
        return {
            'domain': domain,
            'city': city,
            'ns_domain': ns_domain,
            'pub_key': pub_key
        }

vpn_manager = VPNManager()

def require_api_key(f):
    """Decorator untuk memerlukan API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            abort(401, description="API key diperlukan")
        
        valid, key_data = vpn_manager.verify_api_key(api_key)
        if not valid:
            abort(401, description="API key tidak valid")
        
        request.api_key_data = key_data
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': str(error.description)}), 401

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error.description)}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Kesalahan server internal'}), 500

# ============ API ENDPOINTS ============

@app.route('/api/v1/info', methods=['GET'])
@require_api_key
def get_server_info():
    """Mendapatkan informasi server"""
    try:
        info = vpn_manager.get_server_info()
        return jsonify({
            'status': 'success',
            'data': info
        })
    except Exception as e:
        app.logger.error(f"Error getting server info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trial/ssh', methods=['POST'])
@require_api_key
# @limiter.limit("5 per minute")  # DISABLED FOR TESTING
def create_trial_ssh():
    """Membuat akun SSH trial"""
    try:
        username = f"Trial-SSH-{random.randint(100, 999)}"
        password = f"ssh{random.randint(1000, 9999)}"
        limit_ip = 2
        expired_days = 1
        
        # Cek apakah user sudah ada
        try:
            subprocess.check_output(['id', username], stderr=subprocess.DEVNULL)
            username = f"Trial-SSH-{random.randint(1000, 9999)}"
        except subprocess.CalledProcessError:
            pass
        
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Buat user SSH
        subprocess.run(['useradd', '-e', expire_str, '-s', '/bin/false', '-M', username], check=True)
        subprocess.run(['bash', '-c', f'echo -e "{password}\\n{password}\\n" | passwd {username}'], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Setup limit IP
        os.makedirs('/etc/kyt/limit/ssh/ip', exist_ok=True)
        with open(f'/etc/kyt/limit/ssh/ip/{username}', 'w') as f:
            f.write(str(limit_ip))
        
        # Simpan ke database SSH
        os.makedirs('/etc/ssh', exist_ok=True)
        with open('/etc/ssh/.ssh.db', 'a') as f:
            f.write(f"### {username} {password} {limit_ip} {expire_str}\n")
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE_TRIAL', 'ssh', request.remote_addr, 
                               f"Akun SSH trial dibuat dengan limit IP: {limit_ip}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun SSH trial berhasil dibuat',
            'data': {
                'username': username,
                'password': password,
                'service_type': 'ssh',
                'ip_limit': limit_ip,
                'expire_date': expire_str,
                'trial_duration': f"{expired_days} hari"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating SSH trial: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts/list', methods=['GET'])
@require_api_key
def list_all_accounts():
    """Mendapatkan daftar semua akun"""
    try:
        service_type = request.args.get('type')
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        if service_type:
            cursor.execute('''
                SELECT username, service_type, created_date, expire_date, quota_gb, ip_limit, is_active 
                FROM accounts WHERE service_type = ?
                ORDER BY created_date DESC
            ''', (service_type,))
        else:
            cursor.execute('''
                SELECT username, service_type, created_date, expire_date, quota_gb, ip_limit, is_active 
                FROM accounts
                ORDER BY created_date DESC
            ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        result = []
        for account in accounts:
            result.append({
                'username': account[0],
                'service_type': account[1],
                'created_date': account[2],
                'expire_date': account[3],
                'quota_gb': account[4],
                'ip_limit': account[5],
                'is_active': bool(account[6])
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        app.logger.error(f"Error listing accounts: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

    check_result "File API berhasil dibuat" "Gagal membuat file API"
fi

# Set permission untuk file API
chmod +x /etc/API/vpn_api.py
chown root:root /etc/API/vpn_api.py

# Buat systemd service
print_info "Membuat systemd service..."
cat > /etc/systemd/system/vpn-api.service << 'EOF'
[Unit]
Description=VPN Management API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/etc/API
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 /etc/API/vpn_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

check_result "Systemd service berhasil dibuat" "Gagal membuat systemd service"

# Reload systemd dan enable service
systemctl daemon-reload
systemctl enable vpn-api
check_result "Service berhasil dienable" "Gagal mengenable service"

# Konfigurasi Nginx sebagai reverse proxy (hanya jika belum ada konfigurasi Xray)
print_info "Mengkonfigurasi Nginx untuk API..."

# Cek apakah sudah ada konfigurasi Xray
if [ -f "/etc/nginx/conf.d/xray.conf" ] || [ -f "/etc/nginx/sites-enabled/xray" ]; then
    print_warning "Konfigurasi Xray sudah ada, menggunakan port alternatif 7000 untuk API"
    API_PORT=7000
else
    API_PORT=5000
fi

# Buat konfigurasi API yang tidak konflik dengan Xray
cat > /etc/nginx/sites-available/vpn-api << EOF
server {
    listen $API_PORT;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Headers untuk CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-API-Key";
        
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-API-Key";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Health check endpoint
    location /health {
        return 200 "API OK";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site di Nginx hanya jika tidak konflik
if [[ "$OS" == "debian" ]]; then
    if [ ! -f "/etc/nginx/sites-enabled/vpn-api" ]; then
        ln -sf /etc/nginx/sites-available/vpn-api /etc/nginx/sites-enabled/
    fi
else
    # Untuk CentOS, copy ke conf.d dengan nama unik
    cp /etc/nginx/sites-available/vpn-api /etc/nginx/conf.d/vpn-api.conf
fi

# Test konfigurasi Nginx dengan fallback
if nginx -t 2>/dev/null; then
    print_ok "Konfigurasi Nginx valid"
else
    print_warning "Konfigurasi Nginx gagal, menggunakan mode standalone"
    rm -f /etc/nginx/sites-enabled/vpn-api
    rm -f /etc/nginx/conf.d/vpn-api.conf
    API_PORT=5000
fi

# Restart services dengan pengecekan
print_info "Memulai services..."

# Cek apakah Xray service sedang berjalan dan jangan ganggu
if systemctl is-active --quiet xray; then
    print_warning "Xray service terdeteksi berjalan, tidak akan restart Nginx"
    # Hanya reload nginx untuk menerapkan konfigurasi baru
    if nginx -t 2>/dev/null; then
        systemctl reload nginx 2>/dev/null || print_warning "Gagal reload Nginx, menggunakan mode standalone"
    fi
else
    # Aman untuk restart nginx
    systemctl restart nginx 2>/dev/null || print_warning "Gagal restart Nginx, menggunakan mode standalone"
fi

systemctl start vpn-api
check_result "VPN API service berhasil dimulai" "Gagal memulai VPN API service"

# Buat script management
print_info "Membuat script management..."
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
check_result "Script management berhasil dibuat" "Gagal membuat script management"

# Buat firewall rules
print_info "Mengkonfigurasi firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 5000/tcp
    if [ "$API_PORT" != "5000" ]; then
        ufw allow $API_PORT/tcp
        print_ok "UFW rule ditambahkan untuk port 5000 dan $API_PORT"
    else
        print_ok "UFW rule ditambahkan untuk port 5000"
    fi
elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=5000/tcp
    if [ "$API_PORT" != "5000" ]; then
        firewall-cmd --permanent --add-port=$API_PORT/tcp
    fi
    firewall-cmd --reload
    print_ok "Firewalld rule ditambahkan untuk port yang diperlukan"
else
    print_warning "Firewall tidak terdeteksi, pastikan port 5000 dan $API_PORT terbuka"
fi

# Ambil IP server
SERVER_IP=$(curl -s ipv4.icanhazip.com 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

# Start API dan ambil default API key
systemctl start vpn-api
sleep 3

DEFAULT_API_KEY=""
if [ -f "/etc/API/api_keys.json" ]; then
    DEFAULT_API_KEY=$(python3 -c "
import json
try:
    with open('/etc/API/api_keys.json', 'r') as f:
        data = json.load(f)
        print(data['default']['key'])
except:
    print('Error reading API key')
" 2>/dev/null)
fi

# Tampilkan informasi instalasi
clear
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        INSTALASI BERHASIL SELESAI!       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📋 INFORMASI API:${NC}"
if [ "$API_PORT" != "5000" ]; then
    echo -e "   🌐 URL API    : http://$SERVER_IP:$API_PORT/api/"
    echo -e "   🌐 Direct API : http://$SERVER_IP:5000"
    echo -e "   ⚠️  Note      : Menggunakan port $API_PORT karena ada Xray"
else
    echo -e "   🌐 URL API    : http://$SERVER_IP:5000"
fi
echo -e "   🔑 API Key    : $DEFAULT_API_KEY"
echo -e "   📝 Log File   : /var/log/api/vpn_api.log"
echo -e "   ⚙️  Config    : /etc/API/"
echo ""
echo -e "${CYAN}🛠️  MANAGEMENT COMMANDS:${NC}"
echo -e "   vpn-api start    - Mulai service"
echo -e "   vpn-api stop     - Hentikan service"  
echo -e "   vpn-api restart  - Restart service"
echo -e "   vpn-api status   - Cek status service"
echo -e "   vpn-api logs     - Lihat log"
echo -e "   vpn-api key      - Lihat API keys"
echo ""
echo -e "${CYAN}📚 CONTOH PENGGUNAAN:${NC}"
echo -e "   # Membuat SSH trial"
if [ "$API_PORT" != "5000" ]; then
    echo -e "   curl -X POST http://$SERVER_IP:$API_PORT/api/v1/trial/ssh \\"
else
    echo -e "   curl -X POST http://$SERVER_IP:5000/api/v1/trial/ssh \\"
fi
echo -e "        -H \"X-API-Key: $DEFAULT_API_KEY\" \\"
echo -e "        -H \"Content-Type: application/json\""
echo ""
echo -e "   # Lihat semua akun"
if [ "$API_PORT" != "5000" ]; then
    echo -e "   curl -X GET http://$SERVER_IP:$API_PORT/api/v1/accounts/list \\"
else
    echo -e "   curl -X GET http://$SERVER_IP:5000/api/v1/accounts/list \\"
fi
echo -e "        -H \"X-API-Key: $DEFAULT_API_KEY\""
echo ""
echo -e "${YELLOW}⚠️  PENTING:${NC}"
echo -e "   - Simpan API Key dengan aman!"
if [ "$API_PORT" != "5000" ]; then
    echo -e "   - Pastikan port $API_PORT dan 5000 terbuka di firewall"
    echo -e "   - API berjalan di port 5000, proxy di port $API_PORT"
    echo -e "   - Konfigurasi dibuat kompatibel dengan Xray"
else
    echo -e "   - Pastikan port 5000 terbuka di firewall"
    echo -e "   - API berjalan di port 5000 langsung"
fi
echo ""
echo -e "${GREEN}🎉 API VPN Management siap digunakan!${NC}"
echo ""

# Simpan informasi ke file
cat > /root/vpn-api-info.txt << EOF
VPN Management API Information
=============================

$(if [ "$API_PORT" != "5000" ]; then
    echo "API URL: http://$SERVER_IP:$API_PORT/api/"
    echo "Direct API URL: http://$SERVER_IP:5000"
    echo "Note: Using port $API_PORT due to Xray compatibility"
else
    echo "API URL: http://$SERVER_IP:5000"
fi)
API Key: $DEFAULT_API_KEY
Log File: /var/log/api/vpn_api.log
Config Dir: /etc/API/

Management Commands:
- vpn-api start
- vpn-api stop  
- vpn-api restart
- vpn-api status
- vpn-api logs
- vpn-api key

Installation Date: $(date)
EOF

print_ok "Informasi instalasi disimpan di /root/vpn-api-info.txt"

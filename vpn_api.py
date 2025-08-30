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

app = Flask(__name__)

# Konfigurasi
API_KEYS_FILE = '/etc/API/api_keys.json'
DATABASE_FILE = '/etc/API/vpn_accounts.db'
LOG_FILE = '/var/log/vpn_api.log'

# Setup logging
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
            self.api_keys = {
                "default": {
                    "key": secrets.token_urlsafe(32),
                    "name": "Default Admin",
                    "permissions": ["all"],
                    "created": datetime.datetime.now().isoformat()
                }
            }
            self.save_api_keys()
    
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

# ============ SSH ENDPOINTS ============

@app.route('/api/v1/ssh/create', methods=['POST'])
@require_api_key
# @limiter.limit("10 per minute")  # DISABLED FOR TESTING
def create_ssh_account():
    """Membuat akun SSH baru"""
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Data JSON diperlukan")
        
        username = data.get('username')
        password = data.get('password')
        limit_ip = data.get('limit_ip', 1)
        expired_days = data.get('expired_days', 30)
        bug_host = data.get('bug_host', 'bug.com')
        
        if not username or not password:
            abort(400, description="Username dan password diperlukan")
        
        # Validasi username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            abort(400, description="Username hanya boleh mengandung huruf, angka, dan underscore")
        
        # Cek apakah user sudah ada
        try:
            subprocess.check_output(['id', username], stderr=subprocess.DEVNULL)
            abort(400, description="Username sudah ada")
        except subprocess.CalledProcessError:
            pass  # User belum ada, lanjutkan
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Buat user SSH
        subprocess.run(['useradd', '-e', expire_str, '-s', '/bin/false', '-M', username], check=True)
        subprocess.run(['bash', '-c', f'echo -e "{password}\\n{password}\\n" | passwd {username}'], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Setup limit IP
        if limit_ip > 0:
            os.makedirs('/etc/kyt/limit/ssh/ip', exist_ok=True)
            with open(f'/etc/kyt/limit/ssh/ip/{username}', 'w') as f:
                f.write(str(limit_ip))
        
        # Simpan ke database SSH
        os.makedirs('/etc/ssh', exist_ok=True)
        with open('/etc/ssh/.ssh.db', 'a') as f:
            f.write(f"### {username} {password} {limit_ip} {expire_str}\n")
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, password, service_type, ip_limit, created_date, expire_date, bug_host)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, 'ssh', limit_ip, datetime.datetime.now().isoformat(), expire_str, bug_host))
        conn.commit()
        conn.close()
        
        # Buat file konfigurasi
        server_info = vpn_manager.get_server_info()
        config_content = f"""
◇━━━━━━━━━━━━━━━━━◇
Format SSH OVPN Account
◇━━━━━━━━━━━━━━━━━◇
Username         : {username}
Password         : {password}
◇━━━━━━━━━━━━━━━━━◇
IP Limit         : {limit_ip}
Host             : {server_info['domain']}
Port OpenSSH     : 443, 80, 22
Port Dropbear    : 443, 109
Port Dropbear WS : 443, 109
Port SSH UDP     : 1-65535
Port SSH WS      : 80, 8080, 8081-9999
Port SSH SSL WS  : 443
Port SSL/TLS     : 400-900
Port OVPN WS SSL : 443
Port OVPN SSL    : 443
Port OVPN TCP    : 1194
Port OVPN UDP    : 2200
BadVPN UDP       : 7100, 7300, 7300
Location         : {server_info['city']}
◇━━━━━━━━━━━━━━━━━◇
Aktif Selama     : {expired_days} Hari
Dibuat Pada      : {datetime.datetime.now().strftime('%d %b, %Y')}
Berakhir Pada    : {expire_date.strftime('%d %b, %Y')}
===============================
Payload WSS: GET wss://{bug_host}/ HTTP/1.1[crlf]Host: {server_info['domain']}[crlf]Upgrade: websocket[crlf][crlf] 
===============================
OVPN Download : https://{server_info['domain']}:81/
===============================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/ssh-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE', 'ssh', request.remote_addr, 
                               f"Akun SSH dibuat dengan limit IP: {limit_ip}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun SSH berhasil dibuat',
            'data': {
                'username': username,
                'password': password,
                'service_type': 'ssh',
                'ip_limit': limit_ip,
                'expire_date': expire_str,
                'config_url': f"https://{server_info['domain']}:81/ssh-{username}.txt"
            }
        })
        
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Error creating SSH account: {str(e)}")
        return jsonify({'error': 'Gagal membuat akun SSH'}), 500
    except Exception as e:
        app.logger.error(f"Error creating SSH account: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/ssh/list', methods=['GET'])
@require_api_key
def list_ssh_accounts():
    """Mendapatkan daftar akun SSH"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, created_date, expire_date, ip_limit, is_active 
            FROM accounts WHERE service_type = 'ssh'
            ORDER BY created_date DESC
        ''')
        accounts = cursor.fetchall()
        conn.close()
        
        result = []
        for account in accounts:
            result.append({
                'username': account[0],
                'created_date': account[1],
                'expire_date': account[2],
                'ip_limit': account[3],
                'is_active': bool(account[4])
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        app.logger.error(f"Error listing SSH accounts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/ssh/delete/<username>', methods=['DELETE'])
@require_api_key
def delete_ssh_account(username):
    """Menghapus akun SSH"""
    try:
        # Cek apakah user ada
        try:
            subprocess.check_output(['id', username], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            abort(404, description="Username tidak ditemukan")
        
        # Hapus user dari sistem
        subprocess.run(['userdel', username], check=True, stderr=subprocess.DEVNULL)
        
        # Hapus dari database SSH
        if os.path.exists('/etc/ssh/.ssh.db'):
            with open('/etc/ssh/.ssh.db', 'r') as f:
                lines = f.readlines()
            with open('/etc/ssh/.ssh.db', 'w') as f:
                for line in lines:
                    if not line.startswith(f'### {username} '):
                        f.write(line)
        
        # Hapus limit IP
        limit_file = f'/etc/kyt/limit/ssh/ip/{username}'
        if os.path.exists(limit_file):
            os.remove(limit_file)
        
        # Hapus file konfigurasi
        config_file = f'/var/www/html/ssh-{username}.txt'
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # Update database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE username = ? AND service_type = ?', (username, 'ssh'))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'DELETE', 'ssh', request.remote_addr, "Akun SSH dihapus")
        
        return jsonify({
            'status': 'success',
            'message': f'Akun SSH {username} berhasil dihapus'
        })
        
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Error deleting SSH account: {str(e)}")
        return jsonify({'error': 'Gagal menghapus akun SSH'}), 500
    except Exception as e:
        app.logger.error(f"Error deleting SSH account: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ TROJAN ENDPOINTS ============

@app.route('/api/v1/trojan/create', methods=['POST'])
@require_api_key
# @limiter.limit("10 per minute")  # DISABLED FOR TESTING
def create_trojan_account():
    """Membuat akun Trojan baru"""
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Data JSON diperlukan")
        
        username = data.get('username')
        expired_days = data.get('expired_days', 30)
        quota_gb = data.get('quota_gb', 0)
        ip_limit = data.get('ip_limit', 1)
        
        if not username:
            abort(400, description="Username diperlukan")
        
        # Validasi username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            abort(400, description="Username hanya boleh mengandung huruf, angka, dan underscore")
        
        # Cek apakah user sudah ada di xray config
        try:
            with open('/etc/xray/config.json', 'r') as f:
                config = f.read()
            if f'"email": "{username}"' in config:
                abort(400, description="Username sudah ada")
        except FileNotFoundError:
            abort(500, description="File konfigurasi Xray tidak ditemukan")
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk Trojan WS
        trojan_ws_entry = f'#! {username} {expire_str}\\n}},{{"password": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#trojanws$/a\\{trojan_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk Trojan gRPC
        trojan_grpc_entry = f'#!# {username} {expire_str}\\n}},{{"password": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#trojangrpc$/a\\{trojan_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        if ip_limit > 0:
            os.makedirs('/etc/kyt/limit/trojan/ip', exist_ok=True)
            with open(f'/etc/kyt/limit/trojan/ip/{username}', 'w') as f:
                f.write(str(ip_limit))
        
        # Setup quota
        if quota_gb > 0:
            os.makedirs('/etc/trojan', exist_ok=True)
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            with open(f'/etc/trojan/{username}', 'w') as f:
                f.write(str(quota_bytes))
        
        # Simpan ke database Trojan
        os.makedirs('/etc/trojan', exist_ok=True)
        with open('/etc/trojan/.trojan.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        trojan_ws_link = f"trojan://{user_uuid}@{domain}:443?path=%2Ftrojan-ws&security=tls&host={domain}&type=ws&sni={domain}#{username}"
        trojan_grpc_link = f"trojan://{user_uuid}@{domain}:443?mode=gun&security=tls&type=grpc&serviceName=trojan-grpc&sni={domain}#{username}"
        trojan_ntls_link = f"trojan://{user_uuid}@{domain}:80?path=%2Ftrojan-ws&security=none&host={domain}&type=ws#{username}"
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Trojan GO/WS
---------------------------------------------------
proxies:
  - name: Trojan-{username}-GO/WS
    server: {domain}
    port: 443
    type: trojan
    password: {user_uuid}
    skip-cert-verify: true
    sni: {domain}
    network: ws
    ws-opts:
      path: /trojan-ws
      headers:
        Host: {domain}
    udp: true

---------------------------------------------------    
# Format Trojan gRPC
---------------------------------------------------
- name: Trojan-{username}-gRPC
  type: trojan
  server: {domain}
  port: 443
  password: {user_uuid}
  udp: true
  sni: {domain}
  skip-cert-verify: true
  network: grpc
  grpc-opts:
    grpc-service-name: trojan-grpc

◇━━━━━━━━━━━━━━━━━◇
   Trojan Account
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
Port TLS         : 400-900
Port none TLS    : 80, 8080, 8081-9999
id               : {user_uuid}
Xray Dns         : {server_info['ns_domain']}
Pubkey           : {server_info['pub_key']}
alterId          : 0
Security         : auto
Network          : ws
Path             : /Multi-Path
ServiceName      : trojan-grpc
Location         : {server_info['city']}
=====================
 Link Akun Trojan                   
=====================
Link TLS         : 
{trojan_ws_link}
=====================
Link GRPC        : 
{trojan_grpc_link}
=====================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/trojan-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'trojan', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE', 'trojan', request.remote_addr, 
                               f"Akun Trojan dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun Trojan berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'trojan',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'links': {
                    'ws_tls': trojan_ws_link,
                    'grpc': trojan_grpc_link,
                    'ws_ntls': trojan_ntls_link
                },
                'config_url': f"https://{domain}:81/trojan-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating Trojan account: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trojan/list', methods=['GET'])
@require_api_key
def list_trojan_accounts():
    """Mendapatkan daftar akun Trojan"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, uuid, created_date, expire_date, quota_gb, ip_limit, is_active 
            FROM accounts WHERE service_type = 'trojan'
            ORDER BY created_date DESC
        ''')
        accounts = cursor.fetchall()
        conn.close()
        
        result = []
        for account in accounts:
            result.append({
                'username': account[0],
                'uuid': account[1],
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
        app.logger.error(f"Error listing Trojan accounts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trojan/delete/<username>', methods=['DELETE'])
@require_api_key
def delete_trojan_account(username):
    """Menghapus akun Trojan"""
    try:
        # Cek apakah user ada di database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT expire_date FROM accounts WHERE username = ? AND service_type = ?', (username, 'trojan'))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            abort(404, description="Username tidak ditemukan")
        
        expire_date = result[0]
        
        # Hapus dari konfigurasi Xray
        subprocess.run(['sed', '-i', f'/^#! {username} {expire_date}/,/^}},{{/d', '/etc/xray/config.json'], check=True)
        subprocess.run(['sed', '-i', f'/^#!# {username} {expire_date}/,/^}},{{/d', '/etc/xray/config.json'], check=True)
        
        # Hapus file terkait
        files_to_remove = [
            f'/etc/trojan/{username}',
            f'/etc/kyt/limit/trojan/ip/{username}',
            f'/var/www/html/trojan-{username}.txt'
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Hapus dari database Trojan
        if os.path.exists('/etc/trojan/.trojan.db'):
            with open('/etc/trojan/.trojan.db', 'r') as f:
                lines = f.readlines()
            with open('/etc/trojan/.trojan.db', 'w') as f:
                for line in lines:
                    if not line.startswith(f'### {username} '):
                        f.write(line)
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Hapus dari database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE username = ? AND service_type = ?', (username, 'trojan'))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'DELETE', 'trojan', request.remote_addr, "Akun Trojan dihapus")
        
        return jsonify({
            'status': 'success',
            'message': f'Akun Trojan {username} berhasil dihapus'
        })
        
    except Exception as e:
        app.logger.error(f"Error deleting Trojan account: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ TRIAL ENDPOINTS ============

@app.route('/api/v1/trial/ssh', methods=['POST'])
@require_api_key
# @limiter.limit("5 per minute")  # DISABLED FOR TESTING
def create_trial_ssh():
    """Membuat akun SSH trial"""
    try:
        # Generate username trial otomatis
        import random
        username = f"Trial-SSH-{random.randint(100, 999)}"
        password = f"ssh{random.randint(1000, 9999)}"
        limit_ip = 2
        expired_days = 1
        bug_host = 'bug.com'
        
        # Cek apakah user sudah ada
        try:
            subprocess.check_output(['id', username], stderr=subprocess.DEVNULL)
            # Jika ada, generate ulang
            username = f"Trial-SSH-{random.randint(1000, 9999)}"
        except subprocess.CalledProcessError:
            pass  # User belum ada, lanjutkan
        
        # Hitung tanggal expire
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
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, password, service_type, ip_limit, created_date, expire_date, bug_host)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, 'ssh', limit_ip, datetime.datetime.now().isoformat(), expire_str, bug_host))
        conn.commit()
        conn.close()
        
        # Buat file konfigurasi
        server_info = vpn_manager.get_server_info()
        config_content = f"""
◇━━━━━━━━━━━━━━━━━◇
Format SSH OVPN Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Username         : {username}
Password         : {password}
◇━━━━━━━━━━━━━━━━━◇
IP Limit         : {limit_ip}
Host             : {server_info['domain']}
Port OpenSSH     : 443, 80, 22
Port Dropbear    : 443, 109
Port Dropbear WS : 443, 109
Port SSH UDP     : 1-65535
Port SSH WS      : 80, 8080, 8081-9999
Port SSH SSL WS  : 443
Port SSL/TLS     : 400-900
Port OVPN WS SSL : 443
Port OVPN SSL    : 443
Port OVPN TCP    : 1194
Port OVPN UDP    : 2200
BadVPN UDP       : 7100, 7300, 7300
Location         : {server_info['city']}
◇━━━━━━━━━━━━━━━━━◇
Aktif Selama     : {expired_days} Hari (TRIAL)
Dibuat Pada      : {datetime.datetime.now().strftime('%d %b, %Y')}
Berakhir Pada    : {expire_date.strftime('%d %b, %Y')}
===============================
Payload WSS: GET wss://{bug_host}/ HTTP/1.1[crlf]Host: {server_info['domain']}[crlf]Upgrade: websocket[crlf][crlf] 
===============================
OVPN Download : https://{server_info['domain']}:81/
===============================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/ssh-{username}.txt', 'w') as f:
            f.write(config_content)
        
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
                'trial_duration': f"{expired_days} hari",
                'config_url': f"https://{server_info['domain']}:81/ssh-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating SSH trial: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trial/trojan', methods=['POST'])
@require_api_key
# @limiter.limit("5 per minute")  # DISABLED FOR TESTING
def create_trial_trojan():
    """Membuat akun Trojan trial"""
    try:
        # Generate username trial otomatis seperti di script asli
        import random
        username = f"Trial-{random.randint(100, 999)}"
        expired_days = 1
        quota_gb = 1
        ip_limit = 3
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk Trojan WS
        trojan_ws_entry = f'#! {username} {expire_str}\\n}},{{"password": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#trojanws$/a\\{trojan_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk Trojan gRPC
        trojan_grpc_entry = f'#!# {username} {expire_str}\\n}},{{"password": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#trojangrpc$/a\\{trojan_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        os.makedirs('/etc/kyt/limit/trojan/ip', exist_ok=True)
        with open(f'/etc/kyt/limit/trojan/ip/{username}', 'w') as f:
            f.write(str(ip_limit))
        
        # Setup quota
        os.makedirs('/etc/trojan', exist_ok=True)
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        with open(f'/etc/trojan/{username}', 'w') as f:
            f.write(str(quota_bytes))
        
        # Simpan ke database Trojan
        with open('/etc/trojan/.trojan.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        trojan_ws_link = f"trojan://{user_uuid}@bugkamu.com:443?path=%2Ftrojan-ws&security=tls&host={domain}&type=ws&sni={domain}#{username}"
        trojan_grpc_link = f"trojan://{user_uuid}@{domain}:443?mode=gun&security=tls&type=grpc&serviceName=trojan-grpc&sni=bug.com#{username}"
        trojan_ntls_link = f"trojan://{user_uuid}@{domain}:80?path=%2Ftrojan-ws&security=none&host={domain}&type=ws#{username}"
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Trojan GO/WS (TRIAL)
---------------------------------------------------
proxies:
  - name: Trojan-{username}-GO/WS
    server: {domain}
    port: 443
    type: trojan
    password: {user_uuid}
    skip-cert-verify: true
    sni: {domain}
    network: ws
    ws-opts:
      path: /trojan-ws
      headers:
        Host: {domain}
    udp: true

---------------------------------------------------    
# Format Trojan gRPC (TRIAL)
---------------------------------------------------
- name: Trojan-{username}-gRPC
  type: trojan
  server: {domain}
  port: 443
  password: {user_uuid}
  udp: true
  sni: {domain}
  skip-cert-verify: true
  network: grpc
  grpc-opts:
    grpc-service-name: trojan-grpc

◇━━━━━━━━━━━━━━━━━◇
   Trojan Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
Port TLS         : 400-900
Port none TLS    : 80, 8080, 8081-9999
id               : {user_uuid}
Xray Dns         : {server_info['ns_domain']}
Pubkey           : {server_info['pub_key']}
alterId          : 0
Security         : auto
Network          : ws
Path             : /Multi-Path
ServiceName      : trojan-grpc
Location         : {server_info['city']}
=====================
 Link Akun Trojan (TRIAL)                
=====================
Link TLS         : 
{trojan_ws_link}
=====================
Link GRPC        : 
{trojan_grpc_link}
=====================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/trojan-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'trojan', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE_TRIAL', 'trojan', request.remote_addr, 
                               f"Akun Trojan trial dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun Trojan trial berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'trojan',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'trial_duration': f"{expired_days} hari",
                'links': {
                    'ws_tls': trojan_ws_link,
                    'grpc': trojan_grpc_link,
                    'ws_ntls': trojan_ntls_link
                },
                'config_url': f"https://{domain}:81/trojan-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating Trojan trial: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trial/vless', methods=['POST'])
@require_api_key
# @limiter.limit("5 per minute")  # DISABLED FOR TESTING
def create_trial_vless():
    """Membuat akun VLess trial"""
    try:
        # Generate username trial otomatis seperti di script asli
        import random
        username = f"WV-{random.randint(100, 999)}"
        expired_days = 1
        quota_gb = 1
        ip_limit = 2
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk VLess WS
        vless_ws_entry = f'#& {username} {expire_str}\\n}},{{"id": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vless$/a\\{vless_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk VLess gRPC
        vless_grpc_entry = f'#&& {username} {expire_str}\\n}},{{"id": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vlessgrpc$/a\\{vless_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        os.makedirs('/etc/kyt/limit/vless/ip', exist_ok=True)
        with open(f'/etc/kyt/limit/vless/ip/{username}', 'w') as f:
            f.write(str(ip_limit))
        
        # Setup quota
        os.makedirs('/etc/vless', exist_ok=True)
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        with open(f'/etc/vless/{username}', 'w') as f:
            f.write(str(quota_bytes))
        
        # Simpan ke database VLess
        with open('/etc/vless/.vless.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        vless_ws_link = f"vless://{user_uuid}@{domain}:443?path=/vless&security=tls&encryption=none&host={domain}&type=ws&serviceName=vless-ws&sni={domain}#{username}"
        vless_grpc_link = f"vless://{user_uuid}@{domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={domain}#{username}"
        vless_ntls_link = f"vless://{user_uuid}@{domain}:80?path=/vless&encryption=none&type=ws#{username}"
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Vless WS TLS (TRIAL)
---------------------------------------------------
proxies:
  - name: Vless-{username}-WS TLS
    server: {domain}
    port: 443
    type: vless
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {domain}
    network: ws
    ws-opts:
      path: /vless
      headers:
        Host: {domain}
    udp: true
    
---------------------------------------------------
# Format Vless gRPC (SNI) (TRIAL)
---------------------------------------------------

- name: Vless-{username}-gRPC (SNI)
  server: {domain}
  port: 443
  type: vless
  uuid: {user_uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: grpc
  grpc-opts:
  grpc-mode: gun
    grpc-service-name: vless-grpc

◇━━━━━━━━━━━━━━━━━◇
   Vless Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username} 
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
port TLS         : 400-900
Port DNS         : 443
Port NTLS        : 80, 8080, 8081-9999
User ID          : {user_uuid}
Xray Dns.        : {server_info['ns_domain']}
Pubkey.          : {server_info['pub_key']}
Encryption       : none
Path TLS         : /vless 
ServiceName      : vless-grpc
Location         : {server_info['city']}
===================
Link Akun Vless (TRIAL)
===================
Link TLS      : 
{vless_ws_link}
===================
Link GRPC     : 
{vless_grpc_link}
===================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/vless-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'vless', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE_TRIAL', 'vless', request.remote_addr, 
                               f"Akun VLess trial dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun VLess trial berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'vless',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'trial_duration': f"{expired_days} hari",
                'links': {
                    'ws_tls': vless_ws_link,
                    'grpc': vless_grpc_link,
                    'ws_ntls': vless_ntls_link
                },
                'config_url': f"https://{domain}:81/vless-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating VLess trial: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/trial/vmess', methods=['POST'])
@require_api_key
# @limiter.limit("5 per minute")  # DISABLED FOR TESTING
def create_trial_vmess():
    """Membuat akun VMess trial"""
    try:
        # Generate username trial otomatis seperti di script asli
        import random
        username = f"WV-{random.randint(100, 999)}"
        expired_days = 1
        quota_gb = 1
        ip_limit = 3
        bug_host = 'bug.com'
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk VMess WS
        vmess_ws_entry = f'### {username} {expire_str}\\n}},{{"id": "{user_uuid}","alterId": 0,"email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vmess$/a\\{vmess_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk VMess gRPC
        vmess_grpc_entry = f'## {username} {expire_str}\\n}},{{"id": "{user_uuid}","alterId": 0,"email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vmessgrpc$/a\\{vmess_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        os.makedirs('/etc/kyt/limit/vmess/ip', exist_ok=True)
        with open(f'/etc/kyt/limit/vmess/ip/{username}', 'w') as f:
            f.write(str(ip_limit))
        
        # Setup quota
        os.makedirs('/etc/vmess', exist_ok=True)
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        with open(f'/etc/vmess/{username}', 'w') as f:
            f.write(str(quota_bytes))
        
        # Simpan ke database VMess
        with open('/etc/vmess/.vmess.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat VMess links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        # VMess WS TLS config
        vmess_ws_config = {
            "v": "2",
            "ps": username,
            "add": domain,
            "port": "443",
            "id": user_uuid,
            "aid": "0",
            "net": "ws",
            "path": "/vmess",
            "type": "none",
            "host": domain,
            "tls": "tls"
        }
        
        # VMess WS Non-TLS config
        vmess_ntls_config = {
            "v": "2",
            "ps": username,
            "add": domain,
            "port": "80",
            "id": user_uuid,
            "aid": "0",
            "net": "ws",
            "path": "/vmess",
            "type": "none",
            "host": domain,
            "tls": "none"
        }
        
        # VMess gRPC config
        vmess_grpc_config = {
            "v": "2",
            "ps": username,
            "add": domain,
            "port": "443",
            "id": user_uuid,
            "aid": "0",
            "net": "grpc",
            "path": "vmess-grpc",
            "type": "none",
            "host": domain,
            "tls": "tls"
        }
        
        import base64
        vmess_ws_link = "vmess://" + base64.b64encode(json.dumps(vmess_ws_config).encode()).decode()
        vmess_ntls_link = "vmess://" + base64.b64encode(json.dumps(vmess_ntls_config).encode()).decode()
        vmess_grpc_link = "vmess://" + base64.b64encode(json.dumps(vmess_grpc_config).encode()).decode()
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Vmess WS TLS (TRIAL)
---------------------------------------------------
proxies:
  - name: Vmess-{username}-WS TLS
    server: {domain}
    port: 443
    type: vmess
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {domain}
    network: ws
    ws-opts:
      path: /vmess
      headers:
        Host: {domain}
    udp: true
    
---------------------------------------------------    
# Format Vmess gRPC (TRIAL)
---------------------------------------------------
proxies:
  - name: Vmess-{username}-gRPC (SNI)
    server: {domain}
    port: 443
    type: vmess
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {domain}
    network: grpc
    grpc-opts:
      grpc-service-name: vmess-grpc
    udp: true

◇━━━━━━━━━━━━━━━━━◇
   Vmess Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
Port TLS         : 400-900
Port none TLS    : 80, 8080, 8081-9999
id               : {user_uuid}
Xray Dns         : {server_info['ns_domain']}
Pubkey           : {server_info['pub_key']}
alterId          : 0
Security         : auto
Network          : ws
Path             : /Multi-Path
Dynamic          : https://{bug_host}/path
ServiceName      : vmess-grpc
Location         : {server_info['city']}
---------------------------------------------------
 Link Akun Vmess (TRIAL)                 
---------------------------------------------------
Link TLS         : 
{vmess_ws_link}
---------------------------------------------------
Link none TLS    : 
{vmess_ntls_link}
---------------------------------------------------
Link GRPC        : 
{vmess_grpc_link}
---------------------------------------------------
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/vmess-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date, bug_host)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'vmess', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str, bug_host))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE_TRIAL', 'vmess', request.remote_addr, 
                               f"Akun VMess trial dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun VMess trial berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'vmess',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'trial_duration': f"{expired_days} hari",
                'bug_host': bug_host,
                'links': {
                    'ws_tls': vmess_ws_link,
                    'ws_ntls': vmess_ntls_link,
                    'grpc': vmess_grpc_link
                },
                'config_url': f"https://{domain}:81/vmess-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating VMess trial: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ VLESS ENDPOINTS ============

@app.route('/api/v1/vless/create', methods=['POST'])
@require_api_key
# @limiter.limit("10 per minute")  # DISABLED FOR TESTING
def create_vless_account():
    """Membuat akun VLess baru"""
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Data JSON diperlukan")
        
        username = data.get('username')
        expired_days = data.get('expired_days', 30)
        quota_gb = data.get('quota_gb', 0)
        ip_limit = data.get('ip_limit', 1)
        
        if not username:
            abort(400, description="Username diperlukan")
        
        # Validasi username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            abort(400, description="Username hanya boleh mengandung huruf, angka, dan underscore")
        
        # Cek apakah user sudah ada di xray config
        try:
            with open('/etc/xray/config.json', 'r') as f:
                config = f.read()
            if f'"email": "{username}"' in config:
                abort(400, description="Username sudah ada")
        except FileNotFoundError:
            abort(500, description="File konfigurasi Xray tidak ditemukan")
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk VLess WS
        vless_ws_entry = f'#& {username} {expire_str}\\n}},{{"id": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vless$/a\\{vless_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk VLess gRPC
        vless_grpc_entry = f'#&& {username} {expire_str}\\n}},{{"id": "{user_uuid}","email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vlessgrpc$/a\\{vless_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        if ip_limit > 0:
            os.makedirs('/etc/kyt/limit/vless/ip', exist_ok=True)
            with open(f'/etc/kyt/limit/vless/ip/{username}', 'w') as f:
                f.write(str(ip_limit))
        
        # Setup quota
        if quota_gb > 0:
            os.makedirs('/etc/vless', exist_ok=True)
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            with open(f'/etc/vless/{username}', 'w') as f:
                f.write(str(quota_bytes))
        
        # Simpan ke database VLess
        os.makedirs('/etc/vless', exist_ok=True)
        with open('/etc/vless/.vless.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        vless_ws_link = f"vless://{user_uuid}@{domain}:443?path=/vless&security=tls&encryption=none&host={domain}&type=ws&serviceName=vless-ws&sni={domain}#{username}"
        vless_grpc_link = f"vless://{user_uuid}@{domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={domain}#{username}"
        vless_ntls_link = f"vless://{user_uuid}@{domain}:80?path=/vless&encryption=none&type=ws#{username}"
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Vless WS TLS
---------------------------------------------------
proxies:
  - name: Vless-{username}-WS TLS
    server: {domain}
    port: 443
    type: vless
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {domain}
    network: ws
    ws-opts:
      path: /vless
      headers:
        Host: {domain}
    udp: true
    
---------------------------------------------------
# Format Vless gRPC (SNI)
---------------------------------------------------

- name: Vless-{username}-gRPC (SNI)
  server: {domain}
  port: 443
  type: vless
  uuid: {user_uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: grpc
  grpc-opts:
  grpc-mode: gun
    grpc-service-name: vless-grpc

◇━━━━━━━━━━━━━━━━━◇
   Vless Accont    
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username} 
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
port TLS         : 400-900
Port DNS         : 443
Port NTLS        : 80, 8080, 8081-9999
User ID          : {user_uuid}
Xray Dns.        : {server_info['ns_domain']}
Pubkey.          : {server_info['pub_key']}
Encryption       : none
Path TLS         : /vless 
ServiceName      : vless-grpc
Location         : {server_info['city']}
===================
Link Akun Vless 
===================
Link TLS      : 
{vless_ws_link}
===================
Link GRPC     : 
{vless_grpc_link}
===================
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/vless-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'vless', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE', 'vless', request.remote_addr, 
                               f"Akun VLess dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun VLess berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'vless',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'links': {
                    'ws_tls': vless_ws_link,
                    'grpc': vless_grpc_link,
                    'ws_ntls': vless_ntls_link
                },
                'config_url': f"https://{domain}:81/vless-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating VLess account: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ VMESS ENDPOINTS ============

@app.route('/api/v1/vmess/create', methods=['POST'])
@require_api_key
# @limiter.limit("10 per minute")  # DISABLED FOR TESTING
def create_vmess_account():
    """Membuat akun VMess baru"""
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Data JSON diperlukan")
        
        username = data.get('username')
        expired_days = data.get('expired_days', 30)
        quota_gb = data.get('quota_gb', 0)
        ip_limit = data.get('ip_limit', 1)
        bug_host = data.get('bug_host', 'bug.com')
        
        if not username:
            abort(400, description="Username diperlukan")
        
        # Validasi username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            abort(400, description="Username hanya boleh mengandung huruf, angka, dan underscore")
        
        # Cek apakah user sudah ada di xray config
        try:
            with open('/etc/xray/config.json', 'r') as f:
                config = f.read()
            if f'"email": "{username}"' in config:
                abort(400, description="Username sudah ada")
        except FileNotFoundError:
            abort(500, description="File konfigurasi Xray tidak ditemukan")
        
        # Generate UUID
        user_uuid = str(uuid.uuid4())
        
        # Hitung tanggal expire
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expired_days)
        expire_str = expire_date.strftime('%Y-%m-%d')
        
        # Tambahkan ke konfigurasi Xray
        # Untuk VMess WS
        vmess_ws_entry = f'### {username} {expire_str}\\n}},{{"id": "{user_uuid}","alterId": 0,"email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vmess$/a\\{vmess_ws_entry}', '/etc/xray/config.json'], check=True)
        
        # Untuk VMess gRPC
        vmess_grpc_entry = f'## {username} {expire_str}\\n}},{{"id": "{user_uuid}","alterId": 0,"email": "{username}"}}'
        subprocess.run(['sed', '-i', f'/#vmessgrpc$/a\\{vmess_grpc_entry}', '/etc/xray/config.json'], check=True)
        
        # Setup limit IP
        if ip_limit > 0:
            os.makedirs('/etc/kyt/limit/vmess/ip', exist_ok=True)
            with open(f'/etc/kyt/limit/vmess/ip/{username}', 'w') as f:
                f.write(str(ip_limit))
        
        # Setup quota
        if quota_gb > 0:
            os.makedirs('/etc/vmess', exist_ok=True)
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            with open(f'/etc/vmess/{username}', 'w') as f:
                f.write(str(quota_bytes))
        
        # Simpan ke database VMess
        os.makedirs('/etc/vmess', exist_ok=True)
        with open('/etc/vmess/.vmess.db', 'a') as f:
            f.write(f"### {username} {expire_str} {user_uuid} {quota_gb} {ip_limit}\n")
        
        # Restart Xray service
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        
        # Buat VMess links
        server_info = vpn_manager.get_server_info()
        domain = server_info['domain']
        
        # VMess WS TLS config
        vmess_ws_config = {
            "v": "2",
            "ps": username,
            "add": bug_host,
            "port": "443",
            "id": user_uuid,
            "aid": "0",
            "net": "ws",
            "path": "/vmess",
            "type": "none",
            "host": domain,
            "tls": "tls"
        }
        
        # VMess WS Non-TLS config
        vmess_ntls_config = {
            "v": "2",
            "ps": username,
            "add": bug_host,
            "port": "80",
            "id": user_uuid,
            "aid": "0",
            "net": "ws",
            "path": "/vmess",
            "type": "none",
            "host": domain,
            "tls": "none"
        }
        
        # VMess gRPC config
        vmess_grpc_config = {
            "v": "2",
            "ps": username,
            "add": domain,
            "port": "443",
            "id": user_uuid,
            "aid": "0",
            "net": "grpc",
            "path": "vmess-grpc",
            "type": "none",
            "host": domain,
            "tls": "tls"
        }
        
        import base64
        vmess_ws_link = "vmess://" + base64.b64encode(json.dumps(vmess_ws_config).encode()).decode()
        vmess_ntls_link = "vmess://" + base64.b64encode(json.dumps(vmess_ntls_config).encode()).decode()
        vmess_grpc_link = "vmess://" + base64.b64encode(json.dumps(vmess_grpc_config).encode()).decode()
        
        # Buat file konfigurasi
        config_content = f"""---------------------------------------------------
# Format Vmess WS TLS
---------------------------------------------------
proxies:
  - name: Vmess-{username}-WS TLS
    server: {domain}
    port: 443
    type: vmess
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {bug_host}
    network: ws
    ws-opts:
      path: /vmess
      headers:
        Host: {domain}
    udp: true
    
---------------------------------------------------
# Format Vmess WS Non TLS
---------------------------------------------------
proxies:
  - name: Vmess-{username}-WS Non TLS
    server: {bug_host}
    port: 80
    type: vmess
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: false
    skip-cert-verify: true
    servername: {domain}
    network: ws
    ws-opts:
      path: /vmess
      headers:
        Host: {domain}
    udp: true
    
# Format Vmess gRPC
---------------------------------------------------
proxies:
  - name: Vmess-{username}-gRPC (SNI)
    server: {domain}
    port: 443
    type: vmess
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {domain}
    network: grpc
    grpc-opts:
      grpc-service-name: vmess-grpc
    udp: true

◇━━━━━━━━━━━━━━━━━◇
   Vmess Account 
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
Port TLS         : 400-900
Port none TLS    : 80, 8080, 8081-9999
id               : {user_uuid}
Xray Dns         : {server_info['ns_domain']}
Pubkey           : {server_info['pub_key']}
alterId          : 0
Security         : auto
Network          : ws
Path             : /Multi-Path
Dynamic          : https://{bug_host}/path
ServiceName      : vmess-grpc
Location         : {server_info['city']}
---------------------------------------------------
 Link Akun Vmess                   
---------------------------------------------------
Link TLS         : 
{vmess_ws_link}
---------------------------------------------------
Link none TLS    : 
{vmess_ntls_link}
---------------------------------------------------
Link GRPC        : 
{vmess_grpc_link}
---------------------------------------------------
"""
        
        os.makedirs('/var/www/html', exist_ok=True)
        with open(f'/var/www/html/vmess-{username}.txt', 'w') as f:
            f.write(config_content)
        
        # Simpan ke database API
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, uuid, service_type, quota_gb, ip_limit, created_date, expire_date, bug_host)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, user_uuid, 'vmess', quota_gb, ip_limit, datetime.datetime.now().isoformat(), expire_str, bug_host))
        conn.commit()
        conn.close()
        
        # Log aktivitas
        vpn_manager.log_activity(username, 'CREATE', 'vmess', request.remote_addr, 
                               f"Akun VMess dibuat dengan quota: {quota_gb}GB, IP limit: {ip_limit}")
        
        return jsonify({
            'status': 'success',
            'message': 'Akun VMess berhasil dibuat',
            'data': {
                'username': username,
                'uuid': user_uuid,
                'service_type': 'vmess',
                'quota_gb': quota_gb,
                'ip_limit': ip_limit,
                'expire_date': expire_str,
                'bug_host': bug_host,
                'links': {
                    'ws_tls': vmess_ws_link,
                    'ws_ntls': vmess_ntls_link,
                    'grpc': vmess_grpc_link
                },
                'config_url': f"https://{domain}:81/vmess-{username}.txt"
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating VMess account: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ GENERAL ENDPOINTS ============

@app.route('/api/v1/accounts/list', methods=['GET'])
@require_api_key
def list_all_accounts():
    """Mendapatkan daftar semua akun"""
    try:
        service_type = request.args.get('type')  # Filter berdasarkan tipe service
        
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

@app.route('/api/v1/accounts/stats', methods=['GET'])
@require_api_key
def get_accounts_stats():
    """Mendapatkan statistik akun"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Total akun per service
        cursor.execute('''
            SELECT service_type, COUNT(*) as count
            FROM accounts
            GROUP BY service_type
        ''')
        service_stats = cursor.fetchall()
        
        # Akun aktif vs tidak aktif
        cursor.execute('''
            SELECT is_active, COUNT(*) as count
            FROM accounts
            GROUP BY is_active
        ''')
        active_stats = cursor.fetchall()
        
        # Akun yang akan expire dalam 7 hari
        expire_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM accounts
            WHERE expire_date <= ? AND is_active = 1
        ''', (expire_date,))
        expiring_soon = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            'service_stats': {row[0]: row[1] for row in service_stats},
            'active_stats': {bool(row[0]): row[1] for row in active_stats},
            'expiring_soon': expiring_soon
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/logs', methods=['GET'])
@require_api_key
def get_activity_logs():
    """Mendapatkan log aktivitas"""
    try:
        limit = request.args.get('limit', 100, type=int)
        username = request.args.get('username')
        action = request.args.get('action')
        service_type = request.args.get('service_type')
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM activity_logs WHERE 1=1'
        params = []
        
        if username:
            query += ' AND username = ?'
            params.append(username)
        
        if action:
            query += ' AND action = ?'
            params.append(action)
        
        if service_type:
            query += ' AND service_type = ?'
            params.append(service_type)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        
        result = []
        for log in logs:
            result.append({
                'id': log[0],
                'username': log[1],
                'action': log[2],
                'service_type': log[3],
                'timestamp': log[4],
                'ip_address': log[5],
                'details': log[6]
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        app.logger.error(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ API KEY MANAGEMENT ============

@app.route('/api/v1/admin/keys', methods=['GET'])
@require_api_key
def list_api_keys():
    """Mendapatkan daftar API keys (hanya key ID dan info)"""
    try:
        # Hanya admin yang bisa melihat daftar keys
        if 'admin' not in request.api_key_data.get('permissions', []) and 'all' not in request.api_key_data.get('permissions', []):
            abort(403, description="Tidak memiliki izin admin")
        
        keys_info = {}
        for key_id, key_data in vpn_manager.api_keys.items():
            keys_info[key_id] = {
                'name': key_data.get('name', ''),
                'permissions': key_data.get('permissions', []),
                'created': key_data.get('created', ''),
                'key_preview': key_data['key'][:8] + '...'  # Hanya tampilkan 8 karakter pertama
            }
        
        return jsonify({
            'status': 'success',
            'data': keys_info
        })
        
    except Exception as e:
        app.logger.error(f"Error listing API keys: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/admin/keys', methods=['POST'])
@require_api_key
def create_api_key():
    """Membuat API key baru"""
    try:
        # Hanya admin yang bisa membuat keys
        if 'admin' not in request.api_key_data.get('permissions', []) and 'all' not in request.api_key_data.get('permissions', []):
            abort(403, description="Tidak memiliki izin admin")
        
        data = request.get_json()
        if not data:
            abort(400, description="Data JSON diperlukan")
        
        name = data.get('name')
        permissions = data.get('permissions', ['read'])
        
        if not name:
            abort(400, description="Nama API key diperlukan")
        
        # Generate key ID dan API key
        key_id = secrets.token_urlsafe(8)
        api_key = secrets.token_urlsafe(32)
        
        # Simpan key baru
        vpn_manager.api_keys[key_id] = {
            'key': api_key,
            'name': name,
            'permissions': permissions,
            'created': datetime.datetime.now().isoformat()
        }
        
        vpn_manager.save_api_keys()
        
        return jsonify({
            'status': 'success',
            'message': 'API key berhasil dibuat',
            'data': {
                'key_id': key_id,
                'api_key': api_key,
                'name': name,
                'permissions': permissions
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error creating API key: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, debug=False)

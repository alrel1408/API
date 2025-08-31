#!/usr/bin/env python3
"""
VLess Service Module untuk AlrelShop API Panel
Mengintegrasikan fungsi-fungsi dari script m-vless
"""

import subprocess
import json
import os
import re
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class VLessService:
    def __init__(self):
        self.domain = self._get_domain()
        self.config_path = "/etc/xray/config.json"
        self.vless_db_path = "/etc/vless/.vless.db"
        self.limit_ip_path = "/etc/kyt/limit/vless/ip"
        self.web_path = "/var/www/html"
        
    def _get_domain(self):
        """Get domain dari config"""
        try:
            with open("/etc/xray/domain", "r") as f:
                return f.read().strip()
        except:
            return "localhost"
    
    def _get_server_info(self):
        """Get server information"""
        try:
            with open("/etc/xray/isp", "r") as f:
                isp = f.read().strip()
        except:
            isp = "Unknown"
            
        try:
            with open("/etc/xray/city", "r") as f:
                city = f.read().strip()
        except:
            city = "Unknown"
            
        try:
            with open("/root/nsdomain", "r") as f:
                ns = f.read().strip()
        except:
            ns = "Unknown"
            
        try:
            with open("/etc/slowdns/server.pub", "r") as f:
                pub = f.read().strip()
        except:
            pub = "Unknown"
            
        return {
            "isp": isp,
            "city": city,
            "ns": ns,
            "pub": pub
        }
    
    def create_account(self, data):
        """Create VLess account baru"""
        try:
            username = data.get('username')
            days = data.get('days', 30)
            quota_gb = data.get('quota_gb', 0)
            ip_limit = data.get('ip_limit', 1)
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            # Check if user exists
            if self._user_exists(username):
                return {"status": "error", "message": "Username sudah ada"}
            
            # Generate UUID
            user_uuid = str(uuid.uuid4())
            
            # Calculate expiry
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Add to Xray config
            self._add_to_xray_config(username, user_uuid, expiry_str)
            
            # Setup IP limit
            if ip_limit > 0:
                os.makedirs(self.limit_ip_path, exist_ok=True)
                with open(f"{self.limit_ip_path}/{username}", "w") as f:
                    f.write(str(ip_limit))
            
            # Setup quota
            if quota_gb > 0:
                quota_bytes = quota_gb * 1024 * 1024 * 1024
                os.makedirs("/etc/vless", exist_ok=True)
                with open(f"/etc/vless/{username}", "w") as f:
                    f.write(str(quota_bytes))
            
            # Add to database
            self._add_to_db(username, expiry_str, user_uuid, quota_gb, ip_limit)
            
            # Create config file
            self._create_config_file(username, user_uuid, quota_gb, ip_limit, days)
            
            # Send to Telegram bot
            self._send_telegram_notification(username, user_uuid, quota_gb, ip_limit, days)
            
            # Restart Xray
            subprocess.run(['systemctl', 'restart', 'xray'], check=True)
            
            return {
                "status": "success",
                "message": "VLess account berhasil dibuat",
                "data": {
                    "username": username,
                    "uuid": user_uuid,
                    "expiry": expiry_str,
                    "quota_gb": quota_gb,
                    "ip_limit": ip_limit,
                    "config_url": f"https://{self.domain}:81/vless-{username}.txt"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating VLess account: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_trial(self, data):
        """Create trial VLess account"""
        try:
            minutes = data.get('minutes', 60)
            username = f"WV-{uuid.uuid4().hex[:3].upper()}"
            user_uuid = str(uuid.uuid4())
            quota_gb = 1
            ip_limit = 2
            
            # Calculate expiry
            expiry_date = datetime.now() + timedelta(minutes=minutes)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Add to Xray config
            self._add_to_xray_config(username, user_uuid, expiry_str)
            
            # Setup IP limit
            os.makedirs(self.limit_ip_path, exist_ok=True)
            with open(f"{self.limit_ip_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/vless", exist_ok=True)
            with open(f"/etc/vless/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Add to database
            self._add_to_db(username, expiry_str, user_uuid, quota_gb, ip_limit)
            
            # Create config file
            self._create_config_file(username, user_uuid, quota_gb, ip_limit, minutes, is_trial=True)
            
            # Send to Telegram bot
            self._send_telegram_notification(username, user_uuid, quota_gb, ip_limit, minutes, is_trial=True)
            
            # Restart Xray
            subprocess.run(['systemctl', 'restart', 'xray'], check=True)
            
            return {
                "status": "success",
                "message": "Trial VLess account berhasil dibuat",
                "data": {
                    "username": username,
                    "uuid": user_uuid,
                    "expiry_minutes": minutes,
                    "quota_gb": quota_gb,
                    "ip_limit": ip_limit,
                    "config_url": f"https://{self.domain}:81/vless-{username}.txt"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating trial VLess account: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_accounts(self):
        """List semua VLess accounts"""
        try:
            accounts = []
            
            if os.path.exists(self.vless_db_path):
                with open(self.vless_db_path, "r") as f:
                    for line in f:
                        if line.startswith("### "):
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                username = parts[1]
                                expiry = parts[2]
                                user_uuid = parts[3]
                                quota_gb = parts[4]
                                ip_limit = parts[5] if len(parts) > 5 else "1"
                                
                                accounts.append({
                                    "username": username,
                                    "expiry": expiry,
                                    "uuid": user_uuid,
                                    "quota_gb": quota_gb,
                                    "ip_limit": ip_limit,
                                    "status": self._get_account_status(username, expiry)
                                })
            
            return {
                "status": "success",
                "data": accounts,
                "total": len(accounts)
            }
            
        except Exception as e:
            logger.error(f"Error listing VLess accounts: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_account(self, data):
        """Delete VLess account"""
        try:
            username = data.get('username')
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            # Remove from Xray config
            self._remove_from_xray_config(username)
            
            # Remove from database
            self._remove_from_db(username)
            
            # Remove files
            for path in [f"/etc/vless/{username}", f"{self.limit_ip_path}/{username}", f"{self.web_path}/vless-{username}.txt"]:
                if os.path.exists(path):
                    os.remove(path)
            
            # Restart Xray
            subprocess.run(['systemctl', 'restart', 'xray'], check=True)
            
            return {
                "status": "success",
                "message": f"VLess account {username} berhasil dihapus"
            }
            
        except Exception as e:
            logger.error(f"Error deleting VLess account: {e}")
            return {"status": "error", "message": str(e)}
    
    def renew_account(self, data):
        """Renew VLess account"""
        try:
            username = data.get('username')
            days = data.get('days', 30)
            new_quota_gb = data.get('quota_gb')
            new_ip_limit = data.get('ip_limit')
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            # Calculate new expiry
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Update Xray config
            self._update_xray_config(username, expiry_str)
            
            # Update IP limit if provided
            if new_ip_limit is not None:
                os.makedirs(self.limit_ip_path, exist_ok=True)
                with open(f"{self.limit_ip_path}/{username}", "w") as f:
                    f.write(str(new_ip_limit))
            
            # Update quota if provided
            if new_quota_gb is not None:
                quota_bytes = new_quota_gb * 1024 * 1024 * 1024
                os.makedirs("/etc/vless", exist_ok=True)
                with open(f"/etc/vless/{username}", "w") as f:
                    f.write(str(quota_bytes))
            
            # Update database
            self._update_db(username, expiry_str)
            
            # Restart Xray
            subprocess.run(['systemctl', 'restart', 'xray'], check=True)
            
            return {
                "status": "success",
                "message": f"VLess account {username} berhasil diperpanjang",
                "data": {
                    "username": username,
                    "expiry": expiry_str,
                    "days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Error renewing VLess account: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_info(self):
        """Get VLess service info"""
        try:
            total_accounts = len(self.list_accounts().get('data', []))
            active_accounts = len([acc for acc in self.list_accounts().get('data', []) if acc.get('status') == 'active'])
            
            return {
                "status": "running",
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "domain": self.domain
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _user_exists(self, username):
        """Check if user exists in Xray config"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    content = f.read()
                    return f'"email": "{username}"' in content
            return False
        except:
            return False
    
    def _add_to_xray_config(self, username, user_uuid, expiry_str):
        """Add user to Xray config using sed like original script"""
        try:
            # Use sed command like original script for vless WS
            vless_ws_entry = f'#& {username} {expiry_str}\n}},{{"id": "{user_uuid}","email": "{username}"}}'
            subprocess.run([
                'sed', '-i', f'/#vless$/a\\{vless_ws_entry}',
                self.config_path
            ], check=True)
            
            # Use sed command like original script for vless gRPC  
            vless_grpc_entry = f'#&& {username} {expiry_str}\n}},{{"id": "{user_uuid}","email": "{username}"}}'
            subprocess.run([
                'sed', '-i', f'/#vlessgrpc$/a\\{vless_grpc_entry}',
                self.config_path
            ], check=True)
                
        except Exception as e:
            logger.error(f"Error adding to Xray config: {e}")
            raise
    
    def _remove_from_xray_config(self, username):
        """Remove user from Xray config using sed like original script"""
        try:
            # Get expiry for the user
            expiry = self._get_user_expiry(username)
            if expiry:
                # Remove vless WS entry
                subprocess.run([
                    'sed', '-i', f'/^#& {username} {expiry}/,/^}},{{/d',
                    self.config_path
                ], check=True)
                
                # Remove vless gRPC entry
                subprocess.run([
                    'sed', '-i', f'/^#&& {username} {expiry}/,/^}},{{/d',
                    self.config_path
                ], check=True)
                
        except Exception as e:
            logger.error(f"Error removing from Xray config: {e}")
            raise
    
    def _update_xray_config(self, username, new_expiry):
        """Update user expiry in Xray config using sed like original script"""
        try:
            # Update vless WS entry
            subprocess.run([
                'sed', '-i', f'/^#& {username}/c\\#& {username} {new_expiry}',
                self.config_path
            ], check=True)
            
            # Update vless gRPC entry  
            subprocess.run([
                'sed', '-i', f'/^#&& {username}/c\\#&& {username} {new_expiry}',
                self.config_path
            ], check=True)
                
        except Exception as e:
            logger.error(f"Error updating Xray config: {e}")
            raise
    
    def _get_user_expiry(self, username):
        """Get user expiry from database"""
        try:
            if os.path.exists(self.vless_db_path):
                with open(self.vless_db_path, "r") as f:
                    for line in f:
                        if line.startswith(f"### {username} "):
                            parts = line.strip().split()
                            if len(parts) >= 3:
                                return parts[2]
            return None
        except:
            return None
    
    def _add_to_db(self, username, expiry, user_uuid, quota_gb, ip_limit):
        """Add user to database"""
        os.makedirs("/etc/vless", exist_ok=True)
        
        # Remove existing entry if any
        self._remove_from_db(username)
        
        # Add new entry
        with open(self.vless_db_path, "a") as f:
            f.write(f"### {username} {expiry} {user_uuid} {quota_gb} {ip_limit}\n")
    
    def _remove_from_db(self, username):
        """Remove user from database"""
        if os.path.exists(self.vless_db_path):
            lines = []
            with open(self.vless_db_path, "r") as f:
                for line in f:
                    if not line.startswith(f"### {username} "):
                        lines.append(line)
            
            with open(self.vless_db_path, "w") as f:
                f.writelines(lines)
    
    def _update_db(self, username, new_expiry):
        """Update user expiry in database"""
        if os.path.exists(self.vless_db_path):
            lines = []
            with open(self.vless_db_path, "r") as f:
                for line in f:
                    if line.startswith(f"### {username} "):
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            parts[2] = new_expiry
                            lines.append(" ".join(parts) + "\n")
                    else:
                        lines.append(line)
            
            with open(self.vless_db_path, "w") as f:
                f.writelines(lines)
    
    def _get_account_status(self, username, expiry):
        """Get account status (active/expired)"""
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            if datetime.now() < expiry_date:
                return 'active'
            else:
                return 'expired'
        except:
            return 'unknown'
    
    def _create_config_file(self, username, user_uuid, quota_gb, ip_limit, duration, is_trial=False):
        """Create VLess config file"""
        server_info = self._get_server_info()
        
        # Generate VLess links
        vless_ws_tls = f"vless://{user_uuid}@{self.domain}:443?path=/vless&security=tls&encryption=none&host={self.domain}&type=ws&serviceName=vless-ws&sni={self.domain}#{username}"
        vless_ws_nontls = f"vless://{user_uuid}@{self.domain}:80?path=/vless&encryption=none&type=ws#{username}"
        vless_grpc = f"vless://{user_uuid}@{self.domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={self.domain}#{username}"
        
        duration_text = f"{duration} Menit" if is_trial else f"{duration} Hari"
        
        config_content = f"""---------------------------------------------------
# Format Vless WS TLS
---------------------------------------------------
proxies:
  - name: Vless-{username}-WS TLS
    server: {self.domain}
    port: 443
    type: vless
    uuid: {user_uuid}
    alterId: 0
    cipher: auto
    tls: true
    skip-cert-verify: true
    servername: {self.domain}
    network: ws
    ws-opts:
      path: /vless
      headers:
        Host: {self.domain}
    udp: true
    
---------------------------------------------------
# Format Vless gRPC (SNI)
---------------------------------------------------
- name: Vless-{username}-gRPC (SNI)
  server: {self.domain}
  port: 443
  type: vless
  uuid: {user_uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {self.domain}
  network: grpc
  grpc-opts:
  grpc-mode: gun
    grpc-service-name: vless-grpc

◇━━━━━━━━━━━━━━━━━◇
   Vless Account    
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username} 
Domain           : {self.domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
port TLS         : 400-900
Port DNS         : 443
Port NTLS        : 80, 8080, 8081-9999
User ID          : {user_uuid}
Xray Dns.        : {server_info['ns']}
Pubkey.          : {server_info['pub']}
Encryption       : none
Path TLS         : /vless 
ServiceName      : vless-grpc
Location         : {server_info['city']}
===================
Link Akun Vless 
===================
Link TLS      : 
{vless_ws_tls}
===================
Link GRPC     : 
{vless_grpc}
===================
Aktif Selama     : {duration_text}
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
Berakhir Pada    : {expiry_date.strftime('%d %b %Y')}
==================="""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/vless-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _send_telegram_notification(self, username, user_uuid, quota_gb, ip_limit, duration, is_trial=False):
        """Send notification to Telegram bot"""
        try:
            # Get bot config
            bot_config = self._get_bot_config()
            if not bot_config:
                return
            
            server_info = self._get_server_info()
            duration_text = f"{duration} Menit" if is_trial else f"{duration} Hari"
            
            # Generate VLess links
            vless_ws_tls = f"vless://{user_uuid}@{self.domain}:443?path=/vless&security=tls&encryption=none&host={self.domain}&type=ws&serviceName=vless-ws&sni={self.domain}#{username}"
            vless_ws_nontls = f"vless://{user_uuid}@{self.domain}:80?path=/vless&encryption=none&type=ws#{username}"
            vless_grpc = f"vless://{user_uuid}@{self.domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={self.domain}#{username}"
            
            message = f"""<code>---------------------------------------------------</code>
<code>      XRAY/VLESS</code>
<code>---------------------------------------------------</code>
<code>Remarks : {username}
Iplimit : {ip_limit}
Domain : {self.domain}
Host XrayDNS: {server_info['ns']}
Pub Key: {server_info['pub']}
Limit Quota : {quota_gb} GB
Port TLS   : 400-900
Port NTLS : 80, 8080, 8081-9999
id  : {user_uuid}
alterId : 0
Security : auto
network : ws or grpc
Path : /vless
Dynamic : https://bug.com/vless
Name  : vless-grpc</code>
<code>---------------------------------------------------</code>
<code> VLESS WS TLS</code>
<code>---------------------------------------------------</code>
<code>{vless_ws_tls}</code>
<code>---------------------------------------------------</code>
<code>VLESS WS NO TLS</code>
<code>---------------------------------------------------</code>
<code>{vless_ws_nontls}</code>
<code>---------------------------------------------------</code>
<code> VLESS gRPC</code>
<code>---------------------------------------------------</code>
<code>{vless_grpc}</code>
<code>---------------------------------------------------</code>
Format OpenClash : https://{self.domain}:81/vless-{username}.txt
<code>---------------------------------------------------</code>
Aktif Selama   : {duration_text}
<code>---------------------------------------------------</code>"""
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{bot_config['key']}/sendMessage"
            data = {
                'chat_id': bot_config['chat_id'],
                'text': message,
                'parse_mode': 'html',
                'disable_web_page_preview': True
            }
            
            subprocess.run(['curl', '-s', '--max-time', '10', '-d', json.dumps(data), url], check=True)
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def _get_bot_config(self):
        """Get Telegram bot configuration"""
        try:
            if os.path.exists("/etc/bot/.bot.db"):
                with open("/etc/bot/.bot.db", "r") as f:
                    for line in f:
                        if line.startswith("#bot# "):
                            parts = line.strip().split()
                            if len(parts) >= 3:
                                return {
                                    'key': parts[1],
                                    'chat_id': parts[2]
                                }
            return None
        except:
            return None

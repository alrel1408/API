#!/usr/bin/env python3
"""
SSH Service Module untuk AlrelShop API Panel
Mengintegrasikan fungsi-fungsi dari script m-sshws dan addssh
"""

import subprocess
import json
import os
import re
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SSHService:
    def __init__(self):
        self.domain = self._get_domain()
        self.ssh_db_path = "/etc/ssh/.ssh.db"
        self.limit_ip_path = "/etc/kyt/limit/ssh/ip"
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
        """Create SSH account baru"""
        try:
            username = data.get('username')
            password = data.get('password')
            days = data.get('days', 30)
            ip_limit = data.get('ip_limit', 1)
            quota_gb = data.get('quota_gb', 0)
            
            if not username or not password:
                return {"status": "error", "message": "Username dan password harus diisi"}
            
            # Check if user exists
            if self._user_exists(username):
                return {"status": "error", "message": "Username sudah ada"}
            
            # Create user
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Create system user
            subprocess.run(['useradd', '-e', expiry_str, '-s', '/bin/false', '-M', username], check=True)
            subprocess.run(['echo', f'{password}\n{password}', '|', 'passwd', username], shell=True, check=True)
            
            # Setup IP limit
            if ip_limit > 0:
                os.makedirs(self.limit_ip_path, exist_ok=True)
                with open(f"{self.limit_ip_path}/{username}", "w") as f:
                    f.write(str(ip_limit))
            
            # Setup quota
            if quota_gb > 0:
                quota_bytes = quota_gb * 1024 * 1024 * 1024
                os.makedirs("/etc/ssh", exist_ok=True)
                with open(f"/etc/ssh/{username}", "w") as f:
                    f.write(str(quota_bytes))
            
            # Add to database
            self._add_to_db(username, password, ip_limit, expiry_str)
            
            # Create config file
            self._create_config_file(username, password, ip_limit, days)
            
            # Send to Telegram bot
            self._send_telegram_notification(username, password, ip_limit, days)
            
            return {
                "status": "success",
                "message": "SSH account berhasil dibuat",
                "data": {
                    "username": username,
                    "password": password,
                    "expiry": expiry_str,
                    "ip_limit": ip_limit,
                    "quota_gb": quota_gb,
                    "config_url": f"https://{self.domain}:81/ssh-{username}.txt"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating SSH account: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_trial(self, data):
        """Create trial SSH account"""
        try:
            minutes = data.get('minutes', 60)
            username = f"WV-{uuid.uuid4().hex[:4].upper()}"
            password = "1"
            ip_limit = 4
            quota_gb = 5
            
            # Create user
            expiry_date = datetime.now() + timedelta(minutes=minutes)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Create system user
            subprocess.run(['useradd', '-e', expiry_str, '-s', '/bin/false', '-M', username], check=True)
            subprocess.run(['echo', f'{password}\n{password}', '|', 'passwd', username], shell=True, check=True)
            
            # Setup IP limit
            os.makedirs(self.limit_ip_path, exist_ok=True)
            with open(f"{self.limit_ip_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/ssh", exist_ok=True)
            with open(f"/etc/ssh/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Add to database
            self._add_to_db(username, password, ip_limit, expiry_str)
            
            # Create config file
            self._create_config_file(username, password, ip_limit, minutes, is_trial=True)
            
            # Send to Telegram bot
            self._send_telegram_notification(username, password, ip_limit, minutes, is_trial=True)
            
            # Schedule deletion
            subprocess.run(['echo', f'userdel -f "{username}"', '|', 'at', 'now', '+', str(minutes), 'minutes'], shell=True)
            
            return {
                "status": "success",
                "message": "Trial SSH account berhasil dibuat",
                "data": {
                    "username": username,
                    "password": password,
                    "expiry_minutes": minutes,
                    "ip_limit": ip_limit,
                    "quota_gb": quota_gb,
                    "config_url": f"https://{self.domain}:81/ssh-{username}.txt"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating trial SSH account: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_accounts(self):
        """List semua SSH accounts"""
        try:
            accounts = []
            
            if os.path.exists(self.ssh_db_path):
                with open(self.ssh_db_path, "r") as f:
                    for line in f:
                        if line.startswith("### "):
                            parts = line.strip().split()
                            if len(parts) >= 4:
                                username = parts[1]
                                password = parts[2]
                                ip_limit = parts[3]
                                # SSH format: ### username password ip_limit expiry_date
                                expiry = " ".join(parts[4:]) if len(parts) > 4 else "Unknown"
                                
                                accounts.append({
                                    "username": username,
                                    "password": password,
                                    "ip_limit": ip_limit,
                                    "expiry": expiry,
                                    "status": self._get_user_status(username)
                                })
            
            return {
                "status": "success",
                "data": accounts,
                "total": len(accounts)
            }
            
        except Exception as e:
            logger.error(f"Error listing SSH accounts: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_account(self, data):
        """Delete SSH account"""
        try:
            username = data.get('username')
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            # Delete system user
            subprocess.run(['userdel', '--force', username], check=True)
            
            # Remove from database
            self._remove_from_db(username)
            
            # Remove files
            for path in [f"/etc/ssh/{username}", f"{self.limit_ip_path}/{username}", f"{self.web_path}/ssh-{username}.txt"]:
                if os.path.exists(path):
                    os.remove(path)
            
            return {
                "status": "success",
                "message": f"SSH account {username} berhasil dihapus"
            }
            
        except Exception as e:
            logger.error(f"Error deleting SSH account: {e}")
            return {"status": "error", "message": str(e)}
    
    def renew_account(self, data):
        """Renew SSH account"""
        try:
            username = data.get('username')
            days = data.get('days', 30)
            new_password = data.get('password')
            new_ip_limit = data.get('ip_limit')
            new_quota_gb = data.get('quota_gb')
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            # Calculate new expiry
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            # Update user expiry
            subprocess.run(['usermod', '-e', expiry_str, username], check=True)
            
            # Update password if provided
            if new_password:
                subprocess.run(['echo', f'{new_password}\n{new_password}', '|', 'passwd', username], shell=True, check=True)
            
            # Update IP limit if provided
            if new_ip_limit is not None:
                os.makedirs(self.limit_ip_path, exist_ok=True)
                with open(f"{self.limit_ip_path}/{username}", "w") as f:
                    f.write(str(new_ip_limit))
            
            # Update quota if provided
            if new_quota_gb is not None:
                quota_bytes = new_quota_gb * 1024 * 1024 * 1024
                os.makedirs("/etc/ssh", exist_ok=True)
                with open(f"/etc/ssh/{username}", "w") as f:
                    f.write(str(quota_bytes))
            
            # Update database
            self._update_db(username, expiry_str)
            
            return {
                "status": "success",
                "message": f"SSH account {username} berhasil diperpanjang",
                "data": {
                    "username": username,
                    "expiry": expiry_str,
                    "days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Error renewing SSH account: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_info(self):
        """Get SSH service info"""
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
        """Check if user exists"""
        try:
            result = subprocess.run(['id', username], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _add_to_db(self, username, password, ip_limit, expiry):
        """Add user to database"""
        os.makedirs("/etc/ssh", exist_ok=True)
        
        # Remove existing entry if any
        self._remove_from_db(username)
        
        # Add new entry - SSH format: ### username password ip_limit expiry_date
        with open(self.ssh_db_path, "a") as f:
            f.write(f"### {username} {password} {ip_limit} {expiry}\n")
    
    def _remove_from_db(self, username):
        """Remove user from database"""
        if os.path.exists(self.ssh_db_path):
            lines = []
            with open(self.ssh_db_path, "r") as f:
                for line in f:
                    if not line.startswith(f"### {username} "):
                        lines.append(line)
            
            with open(self.ssh_db_path, "w") as f:
                f.writelines(lines)
    
    def _update_db(self, username, new_expiry):
        """Update user expiry in database"""
        if os.path.exists(self.ssh_db_path):
            lines = []
            with open(self.ssh_db_path, "r") as f:
                for line in f:
                    if line.startswith(f"### {username} "):
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            # SSH format: ### username password ip_limit expiry_date
                            # Replace everything from index 4 onwards with new_expiry
                            new_line = f"### {parts[1]} {parts[2]} {parts[3]} {new_expiry}\n"
                            lines.append(new_line)
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
            
            with open(self.ssh_db_path, "w") as f:
                f.writelines(lines)
    
    def _get_user_status(self, username):
        """Get user status (active/expired/locked)"""
        try:
            result = subprocess.run(['passwd', '-S', username], capture_output=True, text=True)
            if result.returncode == 0:
                status_line = result.stdout.strip()
                if 'L' in status_line:
                    return 'locked'
                elif 'P' in status_line:
                    return 'active'
                else:
                    return 'expired'
            return 'unknown'
        except:
            return 'unknown'
    
    def _create_config_file(self, username, password, ip_limit, duration, is_trial=False):
        """Create SSH config file"""
        server_info = self._get_server_info()
        
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
Format SSH OVPN Account
◇━━━━━━━━━━━━━━━━━◇
Username         : {username}
Password         : {password}
◇━━━━━━━━━━━━━━━━━◇
IP Limit         : {ip_limit}
Host             : {self.domain}
Port OpenSSH     : 443, 80, 22
Port Dropbear    : 443, 109
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
ISP              : {server_info['isp']}
Host Slowdns     : {server_info['ns']}
Pub Key          : {server_info['pub']}
◇━━━━━━━━━━━━━━━━━◇
Aktif Selama     : {duration} {'Menit' if is_trial else 'Hari'}
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
Berakhir Pada    : {datetime.now().strftime('%d %b %Y')}
===============================
Payload WSS: GET wss://bug.com/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf] 
===============================
OVPN Download : https://{self.domain}:81/
==============================="""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/ssh-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _send_telegram_notification(self, username, password, ip_limit, duration, is_trial=False):
        """Send notification to Telegram bot"""
        try:
            # Get bot config
            bot_config = self._get_bot_config()
            if not bot_config:
                return
            
            server_info = self._get_server_info()
            duration_text = f"{duration} Menit" if is_trial else f"{duration} Hari"
            
            message = f"""<code>---------------------------------------------------</code>
<code>SSH OVPN Account</code>
<code>---------------------------------------------------</code>
<code>Username : {username}</code>
<code>Password : {password}</code>
<code>Limit IP : {ip_limit}</code>
<code>Host : {self.domain}</code>
<code>Port OpenSSH : 443, 80, 22</code>
<code>Port Dropbear : 443, 109</code>
<code>Port SSH WS : 80, 8080, 8081-9999</code>
<code>Port SSH UDP : 1-65535</code>
<code>Port SSH SSL WS : 443</code>
<code>Port SSL/TLS : 400-900</code>
<code>Port OVPN WS SSL : 443</code>
<code>Port OVPN SSL : 443</code>
<code>Port OVPN TCP : 443, 1194</code>
<code>Port OVPN UDP : 2200</code>
<code>BadVPN UDP : 7100, 7300, 7300</code>
<code>Host Slowdns : {server_info['ns']}</code>
<code>Pub Key : {server_info['pub']}</code>
<code>---------------------------------------------------</code>
<code>Port 80 : {self.domain}:80@{username}:{password}</code>
<code>Port 443 : {self.domain}:443@{username}:{password}</code>
<code>Udp Custom : {self.domain}:1-65535@{username}:{password}</code>
<code>---------------------------------------------------</code>
<code>Payload WSS :</code>
<code>GET wss://bug.com/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf]</code>
<code>---------------------------------------------------</code>
<code>PAYLOAD TLS :</code>
<code>GET wss://[host]/ HTTP/1.1[crlf]Host: [host][crlf]Connection: Upgrade[crlf]User-Agent: [ua][crlf]Upgrade: websocket[crlf][crlf]</code>
<code>---------------------------------------------------</code>
OVPN Download : https://{self.domain}:81/
<code>---------------------------------------------------</code>
<code>Save Link Account :</code>https://{self.domain}:81/ssh-{username}.txt
<code>---------------------------------------------------</code>
Aktif Selama : {duration_text}
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

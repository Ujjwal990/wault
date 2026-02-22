#!/bin/bash
# ══════════════════════════════════════════════════
#  Wault — AWS EC2 Free Tier Setup Script
#  Run as: sudo bash setup.sh
#  Tested on: Ubuntu 22.04 LTS (t2.micro / t3.micro)
# ══════════════════════════════════════════════════
set -e

APP_USER="ubuntu"
APP_DIR="/home/$APP_USER/wault"
DOMAIN="your-domain.com"   # ← change this OR use your EC2 public IP

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Wault Setup — Family Document Vault"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. System packages
apt-get update -y
apt-get install -y python3-pip python3-venv nginx git certbot python3-certbot-nginx

# 2. App directory (code should already be here)
if [ ! -d "$APP_DIR" ]; then
  echo "ERROR: $APP_DIR not found. Upload your code first."
  exit 1
fi
chown -R $APP_USER:$APP_USER "$APP_DIR"

# 3. Python virtualenv
sudo -u $APP_USER python3 -m venv "$APP_DIR/.venv"
sudo -u $APP_USER "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo -u $APP_USER "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# 4. .env file (copy from .env.example if not present)
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "⚠️  Created .env from .env.example — please edit it: nano $APP_DIR/.env"
fi

# 5. Django setup
cd "$APP_DIR"
sudo -u $APP_USER "$APP_DIR/.venv/bin/python" manage.py migrate --no-input
sudo -u $APP_USER "$APP_DIR/.venv/bin/python" manage.py collectstatic --no-input

# Create superuser (non-interactive)
echo "Creating Django superuser — you will be prompted."
sudo -u $APP_USER "$APP_DIR/.venv/bin/python" manage.py createsuperuser

# 6. Gunicorn systemd service
cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/wault.service
systemctl daemon-reload
systemctl enable wault
systemctl start wault

# 7. Nginx config
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/wault
# Replace placeholder domain
sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/wault
ln -sf /etc/nginx/sites-available/wault /etc/nginx/sites-enabled/wault
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "✅  Wault is running!"
echo "   → http://$DOMAIN"
echo ""
echo "Next steps:"
echo "  1. Edit .env:  nano $APP_DIR/.env"
echo "  2. Upload your service_account.json to $APP_DIR/"
echo "  3. Free SSL:   certbot --nginx -d $DOMAIN"
echo "  4. Restart:    systemctl restart wault"

#!/usr/bin/env bash
# Run on a fresh Ubuntu 24.04 VM as root (sudo -i first).
# Tested on GCP e2-small, Ubuntu 24.04.
#
# BEFORE RUNNING: change DB_PASSWORD to something strong.
# The domain below is the current testing subdomain — update to client's
# domain when they are ready to go live.

set -e

DOMAIN="feritesteel.janavshah.com"
REPO_URL="https://github.com/janav3036/ferrite-steel.git"
APP_DIR="/var/www/ferite_steel"
DB_NAME="ferite_steel_db"
DB_USER="ferite_user"
DB_PASSWORD="CHOOSE_A_STRONG_PASSWORD"

# ── 1. System packages ────────────────────────────────────────────────────────
apt update && apt upgrade -y
apt install -y \
    python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
    nginx \
    certbot python3-certbot-nginx \
    git \
    libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0

# ── 2. PostgreSQL — create DB and user ───────────────────────────────────────
sudo -u postgres psql <<SQL
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT ALL ON SCHEMA public TO $DB_USER;
SQL

# ── 3. Clone repo and set up virtualenv ──────────────────────────────────────
mkdir -p $APP_DIR
git clone $REPO_URL $APP_DIR
cd $APP_DIR

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# ── 4. Create .env file — STOP HERE and fill it in ───────────────────────────
cp .env.example .env
echo ""
echo "=========================================================="
echo "  STOP. Fill in your .env file before continuing."
echo "  Run:  nano $APP_DIR/.env"
echo ""
echo "  Values to set:"
echo "    SECRET_KEY          — generate one: python -c \"import secrets; print(secrets.token_hex(50))\""
echo "    DEBUG               — False"
echo "    ALLOWED_HOSTS       — $DOMAIN"
echo "    CSRF_TRUSTED_ORIGINS — https://$DOMAIN"
echo "    DB_PASSWORD         — $DB_PASSWORD"
echo "    TOGETHER_API_KEY    — your together.ai key"
echo ""
echo "  After saving .env, run the remaining steps manually (see below)."
echo "=========================================================="
exit 0

# ── 5. After filling .env — run these manually ───────────────────────────────
#
#   cd $APP_DIR && source .venv/bin/activate
#   python manage.py collectstatic --noinput
#   python manage.py migrate
#   python manage.py createsuperuser

# ── 6. Gunicorn log directory ─────────────────────────────────────────────────
#   mkdir -p /var/log/gunicorn
#   chown www-data:www-data /var/log/gunicorn

# ── 7. Gunicorn systemd service ───────────────────────────────────────────────
#   cp $APP_DIR/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
#   systemctl daemon-reload
#   systemctl enable gunicorn
#   systemctl start gunicorn

# ── 8. Nginx ──────────────────────────────────────────────────────────────────
#   cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/ferite_steel
#   sed -i "s/YOURDOMAIN.COM/$DOMAIN/g" /etc/nginx/sites-available/ferite_steel
#   ln -s /etc/nginx/sites-available/ferite_steel /etc/nginx/sites-enabled/
#   rm -f /etc/nginx/sites-enabled/default
#   nginx -t && systemctl restart nginx

# ── 9. SSL via Let's Encrypt ──────────────────────────────────────────────────
#   certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m janavdshah30@gmail.com
#   (auto-renewal is configured automatically by certbot)

# ── 10. Cron — poll_emails every minute ──────────────────────────────────────
#   (crontab -u www-data -l 2>/dev/null; echo "* * * * * $APP_DIR/.venv/bin/python $APP_DIR/manage.py poll_emails --scheduled >> /var/log/ferite_poll.log 2>&1") | crontab -u www-data -
#
#   echo ">>> Done. Visit https://$DOMAIN"

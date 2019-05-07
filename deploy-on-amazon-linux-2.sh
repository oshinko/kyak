# PostgreSQL
sudo yum install postgresql-server -y
sudo postgresql-setup initdb
sudo bash -c "cat << EOF > /var/lib/pgsql/data/pg_hba.conf
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF"
sudo systemctl enable postgresql.service
sudo systemctl start postgresql.service

# Python
sudo yum install python3 -y
wget https://raw.githubusercontent.com/oshinko/kyak/draft/requirements.txt -O requirements.txt
python3 -m venv .venv
.venv/bin/python -m pip install -U pip -r requirements.txt

# WSGI
wget https://raw.githubusercontent.com/oshinko/kyak/draft/app.py -O app.py
wget https://raw.githubusercontent.com/oshinko/kyak/draft/example.kyak -O .kyak
sed -i -e "s/secret.*/secret $1/" .kyak
sed -i -e "s|database.*|database postgresql://postgres@localhost/postgres|" .kyak
.venv/bin/python -c "from app import db; db.create_all()"
wget https://raw.githubusercontent.com/oshinko/kyak/draft/index.html -O index.html
sudo bash -c "cat << EOF > /etc/systemd/system/kyak.service
[Unit]
Description=Kyak

[Service]
WorkingDirectory=/home/ec2-user
ExecStart=/home/ec2-user/.venv/bin/gunicorn -w 4 app:app --bind unix:/home/ec2-user/gunicorn.sock
Restart=always
Type=simple
User=ec2-user

[Install]
WantedBy=multi-user.target
EOF"
sudo systemctl daemon-reload
sudo systemctl enable kyak.service
sudo systemctl start kyak.service

# Nginx
sudo amazon-linux-extras install nginx1.12 -y
sudo bash -c "cat << 'EOF' > /etc/nginx/nginx.conf
# ref: https://github.com/benoitc/gunicorn/blob/master/examples/nginx.conf
worker_processes 1;

user ec2-user ec2-user;
error_log  /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
  worker_connections 1024; # increase if you have lots of clients
  accept_mutex off; # set to 'on' if nginx worker_processes > 1
  use epoll;
}

http {
  include mime.types;
  default_type application/octet-stream;
  access_log /var/log/nginx/access.log combined;
  sendfile on;

  upstream app_server {
    server unix:/home/ec2-user/gunicorn.sock fail_timeout=0;
  }

  server {
    listen 80 default_server deferred;
    client_max_body_size 4G;

    keepalive_timeout 5;

    location / {
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_set_header Host \$http_host;
      proxy_redirect off;
      proxy_pass http://app_server;
    }
  }
}
EOF"
sudo systemctl enable nginx.service
sudo systemctl start nginx.service

sudo yum install git postgresql-server python3 -y
sudo postgresql-setup initdb
sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.org
sudo bash -c "cat << EOF > /var/lib/pgsql/data/pg_hba.conf
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF"
sudo systemctl enable postgresql.service
sudo systemctl start postgresql.service
wget https://raw.githubusercontent.com/oshinko/kyak/draft/requirements.txt
python3 -m venv .venv
.venv/bin/python -m pip install -U pip -r requirements.txt
wget https://raw.githubusercontent.com/oshinko/kyak/draft/app.py
wget https://raw.githubusercontent.com/oshinko/kyak/draft/example.kyak -O .kyak
sed -i -e "s|database.*|database postgresql://postgres@localhost/postgres|" .kyak
.venv/bin/python -c "from app import db; db.create_all()"
wget https://raw.githubusercontent.com/oshinko/kyak/draft/index.html
wget https://raw.githubusercontent.com/oshinko/kyak/draft/kyak.service
sudo mv kyak.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kyak.service
sudo systemctl start kyak.service

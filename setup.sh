#!/bin/bash

SERVICE_NAME=file-search-server
SERVICE_FILE=/etc/systemd/system/$SERVICE_NAME.service
LOG_FILE=/var/log/file_search_server.log

echo "[1/3] Creating log file at $LOG_FILE..."
sudo touch $LOG_FILE
sudo chmod 666 $LOG_FILE

echo "[2/3] Creating systemd service file..."

cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=Fast Concurrent File Search Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)/src
ExecStart=/usr/bin/python3 -m main
Restart=always
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF

echo "[3/3] Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "✅ Setup complete. Use 'sudo systemctl status $SERVICE_NAME' to check status."

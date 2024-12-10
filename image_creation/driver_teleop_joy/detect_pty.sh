# detect_pty.sh
#!/bin/bash

#read the PTY path recorded by supervisor.py
PTY=$(cat /tmp/supervisor_pty 2>/dev/null)

if [ -z "$PTY" ] || [ ! -e "$PTY" ]; then
    echo "Error: PTY not found or invalid"
    exit 1
fi

#update docker-compose.override.yml with the detected PTY
cat > docker-compose.override.yml <<EOF
services:
  ros2_robotont_driver:
    volumes:
      - "${PTY}:/dev/ttyACM0"
EOF

echo "Updated docker-compose.override.yml with PTY: ${PTY}"

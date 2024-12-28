# detect_pty.sh
#!/bin/bash

#read the PTY path recorded by supervisor.py
PTY=$(cat /tmp/supervisor_pty 2>/dev/null)

if [ -z "$PTY" ] || [ ! -e "$PTY" ]; then
    echo "Error: PTY not found or invalid"
    exit 1
fi


#use the override file path from the environment variable, or default to current behavior
OVERRIDE_FILE=${OVERRIDE_FILE:-docker-compose.override.yml}

#update the docker-compose.override.yml with the detected PTY
cat > "$OVERRIDE_FILE" <<EOF
services:
  ros2_robotont_driver:
    volumes:
      - "${PTY}:/dev/ttyACM0"
EOF

echo "Updated ${OVERRIDE_FILE} with PTY: ${PTY}"
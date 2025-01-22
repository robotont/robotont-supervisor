import os
import pty
import serial
import subprocess
import threading
import time
import select
import glob
from dotenv import load_dotenv
import docker
from flask import Flask, request, jsonify, render_template

#load environment variables from .env file
load_dotenv()

#initialize the Docker client
docker_client = docker.from_env()

#flask app
app = Flask(__name__)

def discover_compose_files(base_dir):
    """
    Dynamically discover all docker-compose.yml files in the given base directory.
    Returns a dictionary mapping service names to their compose file paths.
    """
    compose_files = {}
    search_path = os.path.join(base_dir, "**", "docker-compose.yml")
    for compose_file in glob.glob(search_path, recursive=True):
        #extract the service name from the parent directory of the compose file
        service_name = os.path.basename(os.path.dirname(compose_file))
        compose_files[service_name] = compose_file
    return compose_files

def run_detect_pty(script_path, override_dir):
    """
    Executes the detect_pty.sh script and ensures docker-compose.override.yml 
    is created in the correct directory.
    """
    try:
        #set the override path dynamically for the script
        env = os.environ.copy()
        override_file_path = os.path.join(override_dir, "docker-compose.override.yml")
        env["OVERRIDE_FILE"] = override_file_path
        
        #run the script and pass the override file path as an argument
        result = subprocess.check_output(
            ["bash", script_path], env=env, text=True).strip()
        
        print(f"detect_pty.sh output: {result}")
        print(f"docker-compose.override.yml created at {override_file_path}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running detect_pty.sh: {e}")
        return None

#get variables from the .env file
CMD_PREFIX = os.getenv("CMD_PREFIX", "CMD")
TIMEOUT_10_MS = float(os.getenv("TIMEOUT_10_MS", 0.01))
BAUD_RATE = int(os.getenv("BAUD_RATE", 115200))
DEVICE_PATH = os.getenv("DEVICE_PATH", "/dev/ttyACM0")
PTY_INFO_FILE = os.getenv("PTY_INFO_FILE", "/tmp/supervisor_pty")
BASE_DIR = os.getenv("BASE_DIR", ".")
COMPOSE_FILES = discover_compose_files(BASE_DIR)

#state to track the serial connection
serial_connected = threading.Event()
serial_device = None

#global shutdown event
shutdown_event = threading.Event()

def monitor_serial_connection(master_fd):
    """
    Monitor the availability of the serial device and reconnect if necessary.
    """
    global serial_device
    while not shutdown_event.is_set():
        try:
            if serial_device is None or not serial_device.is_open:
                print(f"Attempting to connect to serial device at {DEVICE_PATH}...")
                serial_device = serial.Serial(port=DEVICE_PATH, baudrate=BAUD_RATE, timeout=TIMEOUT_10_MS)
                serial_connected.set()
                print(f"Connected to serial device at {DEVICE_PATH}")
                #start communication threads
                serial_to_pty_thread = threading.Thread(target=serial_to_pty, args=(serial_device, master_fd), daemon=True)
                pty_to_serial_thread = threading.Thread(target=pty_to_serial, args=(master_fd, serial_device), daemon=True)
                serial_to_pty_thread.start()
                pty_to_serial_thread.start()
        except serial.SerialException:
            print(f"Serial device {DEVICE_PATH} not available. Retrying in 30 seconds...")
            serial_connected.clear()
            time.sleep(30)
        except Exception as e:
            print(f"Error in monitor_serial_connection: {e}")
            time.sleep(30)


def list_containers(compose_file_path):
    """
    List all containers for a specific docker-compose file.
    """
    try:
        result = subprocess.check_output(
            ["docker", "compose", "-f", compose_file_path, "ps"], text=True
        )
        print("testlist")
        return result
    except subprocess.CalledProcessError as e:
        return f"Error listing containers: {e}"
    
def start_container(service_name, compose_file_path):
    """
    Start a container service by name using the specified docker-compose file.
    Before starting, run detect_pty.sh if it exists in the service's directory.
    """
    service_dir = os.path.dirname(compose_file_path)
    detect_pty_script = os.path.join(service_dir, "detect_pty.sh")
    detected_pty = None

    #run detect_pty.sh if it exists and create the override file in the service directory
    if os.path.exists(detect_pty_script):
        detected_pty = run_detect_pty(detect_pty_script, service_dir)

    try:
        env = os.environ.copy()
        if detected_pty:
            env["DETECTED_PTY"] = detected_pty  #set detected PTY as an environment variable

        result = subprocess.check_output(
            ["docker", "compose", "-f", compose_file_path, "up", "-d", service_name],
            env=env,
            text=True,
        )
        print(f"Service {service_name} started.")
        return f"Service {service_name} started."
    except subprocess.CalledProcessError as e:
        return f"Error starting service {service_name}: {e}"

    
def stop_container(service_name, compose_file_path):
    """
    Stop a container service by name using the specified docker-compose file.
    """
    try:
        result = subprocess.check_output(
            ["docker", "compose", "-f", compose_file_path, "stop", service_name], text=True
        )
        print(f"Service {service_name} stopped.")
        return f"Service {service_name} stopped."
    except subprocess.CalledProcessError as e:
        return f"Error stopping service {service_name}: {e}"


def execute_command(command):
    """
    Executes a shell command and returns the output or error message.
    """
    try:
        output = subprocess.check_output(command, shell=True, text=True)
        print(f"Command executed successfully: {output.strip()}")
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command execution failed: {e}")
        return f"Error: {e}"


def filter_and_process_data(raw_data):
    """
    Filters incoming data. Executes commands prefixed with CMD.
    """
    raw_data = raw_data.strip()
    if raw_data.startswith(CMD_PREFIX):
        print(raw_data)
        command = raw_data[len(CMD_PREFIX):].strip()
        parts = command.split()
        if len(parts) < 1:
            return "Invalid command."
            print("invalid command received")
        
        cmd = parts[0]
        if cmd == "list":
            print("serial-list-filterandprocessdata")
            containers = {service: list_containers(compose_file) for service, compose_file in COMPOSE_FILES.items()}
            return "\n".join([f"{service}: {containers}" for service, containers in containers.items()])
        elif cmd == "start" and len(parts) > 1:
            service_name = parts[1]
            compose_file = COMPOSE_FILES.get(service_name)
            if not compose_file:
                return f"Service {service_name} not found."
            return start_container(service_name, compose_file)
        elif cmd == "stop" and len(parts) > 1:
            service_name = parts[1]
            compose_file = COMPOSE_FILES.get(service_name)
            if not compose_file:
                return f"Service {service_name} not found."
            return stop_container(service_name, compose_file)
        else:
            return f"Unknown command: {cmd}"
    return raw_data if raw_data else None


def serial_to_pty(serial_device, master_fd):
    """
    Reads data from the serial device, filters it, and writes to the PTY.
    """
    while not shutdown_event.is_set():
        try:
            raw_data = serial_device.readline().decode("utf-8", errors="ignore")
            if raw_data.strip():  #avoid empty lines
                #print(f"Received from device: {raw_data.strip()}")
                filtered_data = filter_and_process_data(raw_data)
                if filtered_data:
                    os.write(master_fd, (filtered_data + "\n").encode())
        except Exception as e:
            print(f"Error in serial-to-PTY communication: {e}")
            time.sleep(1)

def pty_to_serial(master_fd, serial_device):
    """
    Reads data from the PTY and forwards it to the serial device.
    """
    while not shutdown_event.is_set():
        try:
            if select.select([master_fd], [], [], TIMEOUT_10_MS)[0]:
                pty_data = os.read(master_fd, 1024)
                if pty_data.strip():  #avoid sending empty data
                   #print(f"Forwarding to device: {pty_data.decode(errors='ignore')}")
                    serial_device.write(pty_data)
        except Exception as e:
            print(f"Error in PTY-to-serial communication: {e}")
            time.sleep(1)

def write_pty_info(slave_name):
    """
    Writes the PTY slave name to a file for reuse by other scripts.
    """
    try:
        with open(PTY_INFO_FILE, "w") as f:
            f.write(slave_name)
        print(f"PTY info written to {PTY_INFO_FILE}")
    except OSError as e:
        print(f"Failed to write PTY info: {e}")


def cleanup_resources(master_fd, slave_fd):
    """
    Cleans up file descriptors and the PTY info file.
    """
    try:
        os.close(master_fd)
        os.close(slave_fd)
        if os.path.exists(PTY_INFO_FILE):
            os.remove(PTY_INFO_FILE)
        print("Cleaned up resources.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

@app.route("/")
def home():
    """
    Render the main web GUI page.
    """
    return render_template("index.html")

@app.route("/containers", methods=["GET"])
def get_containers():
    """
    List all containers for all services.
    """
    results = {}
    for service, compose_file in COMPOSE_FILES.items():
        results[service] = list_containers(compose_file)
    return jsonify(results)

@app.route("/containers/<service>", methods=["GET"])
def get_service_containers(service):
    """
    List containers for a specific service.
    """
    compose_file = COMPOSE_FILES.get(service)
    if not compose_file:
        return jsonify({"error": f"Service '{service}' not found"}), 404
    result = list_containers(compose_file)
    return jsonify({service: result})


@app.route("/containers/start", methods=["POST"])
def start_container_route():
    """
    Start a container by service name.
    """
    service_name = request.json.get("name")
    compose_file = COMPOSE_FILES.get(service_name)
    if not service_name or not compose_file:
        return jsonify({"error": f"Invalid service name: {service_name}"}), 400
    result = start_container(service_name, compose_file)
    return jsonify({"message": result})

@app.route("/containers/stop", methods=["POST"])
def stop_container_route():
    """
    Stop a container by service name.
    """
    service_name = request.json.get("name")
    compose_file = COMPOSE_FILES.get(service_name)
    if not service_name or not compose_file:
        return jsonify({"error": f"Invalid service name: {service_name}"}), 400
    result = stop_container(service_name, compose_file)
    return jsonify({"message": result})
    

def run_web_interface():
    """
    Start the Flask web server.
    """
    app.run(host="0.0.0.0", port=5000)

def main():
    #create a PTY pair
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    print(f"PTY created - Master: {os.ttyname(master_fd)}, Slave: {slave_name}")

    #write PTY info to file
    write_pty_info(slave_name)

    #start Flask web server in a separate thread
    web_thread = threading.Thread(target=run_web_interface, daemon=True)
    web_thread.start()

    #monitor serial connection
    monitor_thread = threading.Thread(target=monitor_serial_connection, args=(master_fd,), daemon=True)
    monitor_thread.start()

    try:
        #keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        shutdown_event.set()  #signal all threads to shut down
        monitor_thread.join()  #wait for the monitor thread to exit
    finally:
        cleanup_resources(master_fd, slave_fd)

if __name__ == "__main__":
    main()

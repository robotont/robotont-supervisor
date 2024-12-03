"""
following code is from https://github.com/ut-ims-robotics/sakk-thesis-2024-robotont-firmware-menu/blob/main/scripts/serialhandler.py
and changed to suit the application here.
"""
import os
import select
import pty
import serial
import subprocess
import threading
import time

TIMEOUT_10_MS = 0.01  #timeout for serial operations

def filter_data(raw_data):
    """
    Filters the incoming data. If it starts with "CMD", execute the command.
    Otherwise, pass the data through.
    """
    raw_data = raw_data.strip()
    if raw_data.startswith("CMD"):
        try:
            #extract and run the command
            command = raw_data[4:]
            output = subprocess.check_output(command, shell=True, text=True)
            print(f"Command Output: {output.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
        return None
    elif raw_data == "":
        return None
    else:
        return raw_data


def serial_communication_tont(master, slave, device_path):
    try:
        with serial.Serial(port=device_path, baudrate=115200, timeout=TIMEOUT_10_MS) as ser_tont:
            while True:
                #read incoming data from the physical serial device
                try:
                    raw_data = ser_tont.readline().decode("utf-8", errors="ignore")
                    print(f"From USB0: {raw_data.strip()}")  #debugging incoming data
                    filtered_data = filter_data(raw_data)
                    if filtered_data:
                        print(f"Filtered Data: {filtered_data}")  #debugging filtered data
                        os.write(master, (filtered_data + "\n").encode())
                except Exception as e:
                    print(f"Error reading from device: {e}")

                #read outgoing data from the PTY
                try:
                    if select.select([master], [], [], 0.1)[0]:
                        outgoing_data = os.read(master, 1024)
                        print(f"Outgoing to USB0: {outgoing_data.decode(errors='ignore')}")  #debug outgoing data
                        ser_tont.write(outgoing_data)
                except Exception as e:
                    print(f"Error writing to device: {e}")
    except serial.SerialException as e:
        print(f"Failed to open serial port {device_path}: {e}")


def main():
    #create a pseudo-terminal pair
    master, slave = pty.openpty()
    pty_slave_name = os.ttyname(slave)
    print(f"Created PTY - Master: {os.ttyname(master)}, Slave: {pty_slave_name}")

    #create a symlink for the slave PTY
    symlink_robotont = "/tmp/robotont"
    try:
        if os.path.islink(symlink_robotont) or os.path.exists(symlink_robotont):
            os.remove(symlink_robotont)
        os.symlink(pty_slave_name, symlink_robotont)
        print(f"Symlink created: {symlink_robotont} -> {pty_slave_name}")
    except OSError as e:
        print(f"Error creating symlink: {e}")
        return

    #start serial communication with the physical device
    device_path = "/dev/ttyUSB0"  #ADJUST IF NEEDED
    tont_thread = threading.Thread(target=serial_communication_tont, args=(master, slave, device_path))
    tont_thread.daemon = True
    tont_thread.start()

    try:
        #main loop to keep the PTY open
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating...")
    finally:
        os.close(master)
        os.close(slave)
        if os.path.exists(symlink_robotont):
            os.remove(symlink_robotont)
        print("Cleaned up resources.")


if __name__ == "__main__":
    main()

import socket
import threading
import json
import time
import random
import sys
from config import SERVERS

# --- Server State Variables ---
state = {}
server_id = -1
role = 'backup'
primary_id = -1
state_lock = threading.Lock()
crash_counter = 0

# --- Communication and Handlers ---

def send_message(host, port, message):
    """Sends a message to a specific host and port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.sendall(json.dumps(message).encode('utf-8'))
        s.close()
        return True
    except socket.error as e:
        # This is expected for crashed servers, so we don't need a loud error
        return False

def handle_client_request(conn, addr):
    """Handles requests from clients."""
    global state, crash_counter, role

    try:
        data = conn.recv(1024).decode('utf-8')
        if not data: # Handle empty data
            return
        
        request = json.loads(data)
        print(f"[{SERVERS[server_id]['name']}] Received client request: {request}")

        # --- Simulate Omission Fault ---
        if random.random() < 0.2 and role == 'primary':
            print(f"[{SERVERS[server_id]['name']}] Simulating omission fault: Request dropped.")
            return

        # --- Process request and update state ---
        with state_lock:
            if request['type'] == 'PUT':
                state[request['key']] = request['value']
                response = {'status': 'success', 'message': f"Key '{request['key']}' set."}
            elif request['type'] == 'GET':
                value = state.get(request['key'], 'Not Found')
                response = {'status': 'success', 'value': value}
            else:
                response = {'status': 'error', 'message': 'Invalid request type.'}
        
        # --- Propagate state change to backups ---
        if role == 'primary':
            for i, server in enumerate(SERVERS):
                if i != server_id:
                    update_message = {
                        'type': 'STATE_UPDATE',
                        'state': state
                    }
                    send_message(server['host'], server['port'] + 1, update_message)

        # --- Simulate Crash Fault ---
        crash_counter += 1
        if crash_counter >= 5 and role == 'primary':
            print(f"[{SERVERS[server_id]['name']}] CRITICAL: CRASH FAULT TRIGGERED. Shutting down...")
            conn.close()
            # It's cleaner to handle this with a flag to exit gracefully
            # For this simple project, sys.exit() is fine.
            sys.exit(1)

        conn.sendall(json.dumps(response).encode('utf-8'))

    except (json.JSONDecodeError, socket.error) as e:
        print(f"Error handling client request from {addr}: {e}")
    finally:
        conn.close()

def handle_replica_message(conn, addr):
    """Handles messages from other servers (replicas)."""
    global state, primary_id, role

    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        message = json.loads(data)
        
        if message['type'] == 'STATE_UPDATE':
            with state_lock:
                state = message['state']
            print(f"[{SERVERS[server_id]['name']}] State updated by primary.")
        elif message['type'] == 'HEARTBEAT':
            # This can be used for more advanced primary detection
            pass

    except (json.JSONDecodeError, socket.error) as e:
        print(f"Error handling replica message from {addr}: {e}")
    finally:
        conn.close()

def client_listener_thread():
    """Listens for incoming client connections."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((SERVERS[server_id]['host'], SERVERS[server_id]['port']))
    s.listen(5)
    print(f"[{SERVERS[server_id]['name']}] Listening for clients on {SERVERS[server_id]['host']}:{SERVERS[server_id]['port']}")
    while True:
        try:
            conn, addr = s.accept()
            # Check role before starting a thread
            if role == 'primary':
                threading.Thread(target=handle_client_request, args=(conn, addr), daemon=True).start()
            else:
                conn.sendall(json.dumps({'status': 'error', 'message': 'I am a backup.'}).encode('utf-8'))
                conn.close()
        except Exception as e:
            print(f"Client listener error: {e}")

def replica_listener_thread():
    """Listens for incoming replica messages."""
    s_replica = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Use a port that is separate from the client port
    s_replica.bind((SERVERS[server_id]['host'], SERVERS[server_id]['port'] + 1))
    s_replica.listen(5)
    print(f"[{SERVERS[server_id]['name']}] Listening for replica messages on {SERVERS[server_id]['host']}:{SERVERS[server_id]['port']+1}")
    while True:
        try:
            conn, addr = s_replica.accept()
            threading.Thread(target=handle_replica_message, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"Replica listener error: {e}")


def primary_heartbeat_thread():
    """Backup servers check if the primary is still alive."""
    global primary_id, role

    while True:
        if role == 'backup':
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                # Attempt to connect to the primary's replica port
                s.connect((SERVERS[primary_id]['host'], SERVERS[primary_id]['port'] + 1))
                s.close()
            except (socket.error, ConnectionRefusedError):
                print(f"[{SERVERS[server_id]['name']}] Primary server is down. Initiating failover...")
                if server_id > primary_id:
                    role = 'primary'
                    primary_id = server_id
                    print(f"[{SERVERS[server_id]['name']}] I am the new primary!")
                else:
                    print(f"[{SERVERS[server_id]['name']}] Another backup will take over. Waiting...")
        time.sleep(5)

# --- Main Logic ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <server_id>")
        sys.exit(1)
    
    server_id = int(sys.argv[1])
    if server_id >= len(SERVERS):
        print("Invalid server ID.")
        sys.exit(1)

    if server_id == 0:
        role = 'primary'
        primary_id = 0
    else:
        primary_id = 0

    print(f"Starting {SERVERS[server_id]['name']} as {role.upper()}...")

    # Start a dedicated thread for each listener
    threading.Thread(target=client_listener_thread, daemon=True).start()
    threading.Thread(target=replica_listener_thread, daemon=True).start()

    if role == 'backup':
        threading.Thread(target=primary_heartbeat_thread, daemon=True).start()

    # The main thread can be kept alive to prevent the process from exiting
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
        sys.exit(0)
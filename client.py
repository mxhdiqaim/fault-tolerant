import socket
import json
import time
from config import SERVERS

def send_request(server, request, timeout=5):
    """Sends a request to a server and handles timeout."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((server['host'], server['port']))
        s.sendall(json.dumps(request).encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        s.close()
        return json.loads(response)
    except (socket.timeout, ConnectionRefusedError) as e:
        print(f"Client: Connection to {server['name']} failed or timed out: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Client: Invalid response from {server['name']}")
        return None

def main():
    primary_server_index = 0
    
    # --- Test Case 1: Demonstrating Crash Fault Tolerance ---
    print("\n--- TEST CASE 1: CRASH FAULT TOLERANCE ---")
    requests_sent = 0
    while requests_sent < 7:
        print(f"\nAttempting request {requests_sent + 1}...")
        
        current_server = SERVERS[primary_server_index]
        request = {
            'type': 'PUT',
            'key': f'key-{requests_sent}',
            'value': f'value-{requests_sent}'
        }

        response = send_request(current_server, request)

        if response and response.get('status') == 'success':
            print(f"Client: Request {requests_sent + 1} succeeded on {current_server['name']}.")
            requests_sent += 1
        elif response and response.get('message') == 'I am a backup.':
            print("Client: Primary server is down or busy. Attempting to find new primary...")
            # Simple failover logic: try the next server in the list
            primary_server_index = (primary_server_index + 1) % len(SERVERS)
            print(f"Client: New primary is now {SERVERS[primary_server_index]['name']}.")
        else:
            print(f"Client: Request {requests_sent + 1} failed. Retrying in 2 seconds...")
            # Failover logic for connection failures
            primary_server_index = (primary_server_index + 1) % len(SERVERS)
            print(f"Client: Assuming failure, trying next server: {SERVERS[primary_server_index]['name']}.")
            time.sleep(2)
        
        time.sleep(1)

    # --- Test Case 2: Demonstrating Omission Fault Tolerance ---
    print("\n--- TEST CASE 2: OMISSION FAULT TOLERANCE ---")
    request = {'type': 'GET', 'key': 'key-3'}
    response = None
    retries = 0
    while not response and retries < 5:
        print(f"Attempting to GET 'key-3' (Retry {retries + 1})...")
        response = send_request(SERVERS[primary_server_index], request)
        if not response:
            print("Client: Did not receive a response. Message may have been dropped. Retrying...")
            retries += 1
            time.sleep(2)

    if response and response.get('status') == 'success':
        print(f"Client: Successfully retrieved value: {response['value']}")
    else:
        print("Client: Failed to retrieve value after multiple retries.")
        
if __name__ == "__main__":
    main()
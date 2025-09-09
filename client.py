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
        print(f"Client: Invalid response from {server['name']}. This might be an empty response or bad data.")
        return None

def main():
    known_primary_id = 0
    
    # Test Case 1: Demonstrating Crash Fault Tolerance
    print("\n--- TEST CASE 1: CRASH FAULT TOLERANCE ---")
    requests_sent = 0
    while requests_sent < 7:
        current_server = SERVERS[known_primary_id]
        print(f"\nAttempting request {requests_sent + 1} to {current_server['name']}...")
        
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
            print(f"Client: {current_server['name']} is a backup. I need to find the new primary.")
            # A backup told us it's not the primary, so we should try the other server
            known_primary_id = (known_primary_id + 1) % len(SERVERS)
            time.sleep(1) # Wait for the new primary to become active
        else:
            # This handles both ConnectionRefusedError and InvalidResponse (from empty data)
            print(f"Client: Request to {current_server['name']} failed. Assuming crash and trying other server.")
            known_primary_id = (known_primary_id + 1) % len(SERVERS)
            time.sleep(2) # Give more time for the other server to take over
        
        time.sleep(1) # Short pause between requests

    # Test Case 2: Demonstrating Omission Fault Tolerance
    print("\n--- TEST CASE 2: OMISSION FAULT TOLERANCE ---")
    request = {'type': 'GET', 'key': 'key-3'}
    response = None
    retries = 0
    while not response and retries < 5:
        print(f"Attempting to GET 'key-3' (Retry {retries + 1})...")
        response = send_request(SERVERS[known_primary_id], request)
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
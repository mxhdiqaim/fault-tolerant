# Fault-Tolerant Key-Value Store

This project implements a simple fault-tolerant key-value store using a primary-backup replication model in Python. It is designed to demonstrate tolerance for crash faults and omission faults.

## Features

- **Primary-Backup Replication**: The system operates with one primary server and one or more backup servers. The primary handles all write operations and replicates the state to the backups.
- **Crash Fault Tolerance**: If the primary server crashes, one of the backup servers is automatically promoted to become the new primary, ensuring the service remains available.
- **Omission Fault Tolerance**: The client is designed to handle cases where messages (requests or responses) are dropped by the network or the server. It implements a retry mechanism to ensure requests are eventually processed.

## Project Structure

- `server.py`: The server application. It can be launched as either a primary or a backup. It handles client requests, state replication, and the failover process.
- `client.py`: The client application that connects to the servers to perform `PUT` and `GET` operations. It includes logic to handle server failures and find the active primary.
- `config.py`: A configuration file that defines the network addresses and ports for all servers in the system.
- `requirements.txt`: A list of Python packages required to run the project.

## Getting Started

### Prerequisites

- Python 3.x
- `pip` for installing packages

### Installation

1.  Clone the repository or download the source code.
2.  It is recommended to use a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

### Running the System

You will need to open three separate terminal windows to run the two servers and the client.

1.  **Start the Primary Server (Server A):**
    In the first terminal, run:

    ```sh
    python server.py 0
    ```

2.  **Start the Backup Server (Server B):**
    In the second terminal, run:

    ```sh
    python server.py 1
    ```

3.  **Run the Client:**
    In the third terminal, run the client script to see the fault tolerance demonstrations in action:
    ```sh
    python client.py
    ```

## How It Works

The client will execute two test cases to demonstrate the system's fault-tolerant capabilities.

1.  **Crash Fault Tolerance**: The client sends a series of `PUT` requests to the primary server. The primary server in `server.py` is programmed to simulate a crash after handling 5 requests. The backup server detects the failure via a heartbeat mechanism, promotes itself to the new primary, and is ready to handle subsequent requests. The client will fail to connect to the old primary, and will automatically switch to the new primary to continue its operations.

2.  **Omission Fault Tolerance**: The primary server in `server.py` is programmed to randomly "drop" incoming requests to simulate an omission fault. The client in `client.py` handles this by implementing a timeout and retry mechanism. If it doesn't receive a response within a certain timeframe, it assumes the message was lost and resends the request.

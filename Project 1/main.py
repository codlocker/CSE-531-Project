import json
import multiprocessing
import os
import sys, getopt
from Branch import Branch, Create_Branch
from Customer import Customer
import socket
import time

from utils import config_logger, log_data

# Initiate logger
logger = config_logger("Main")
THREAD_CONCURRENCY=5
WAIT_TIME_IN_SECONDS = 3

def parse_json(input_file_path: str):
    try:
        with open(input_file_path) as f:
            events = json.load(f)
    except Exception as e:
        print(e)
        exit(1)

    return events

def segregate_events(transactions: list):
    b = []
    c = []
    for transaction in transactions:
        if transaction['type'] == 'branch':
            branch = Branch(
                id=transaction['id'],
                balance=transaction['balance'],
                branches=[])
            b.append(branch)
        elif transaction['type'] == 'customer':
            customer = Customer(
                id=transaction['id'],
                events=transaction['events']
            )
            c.append(customer)
    branch_ids = [br.id for br in b]
    for br in b:
        br.branches = branch_ids

    return b, c

def Allocate_Port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        s.listen(1)
        free_port = s.getsockname()[1]
    return free_port

if __name__ == "__main__":
    argumentList = sys.argv[1:]

    # Options
    options = "hio"

    # Long options
    long_options = ["Help", "Input", "Output"]
    
    input_file = "input.json"
    output_file = "output.json"

    for cur_arg, cur_val in argumentList:
        if cur_arg in ("-h", "--Help"):
            log_data(
                logger=logger,
                message="Options:\n -i / --Input\t Input json file\n -o / -- Output\t Output json file")
        elif cur_arg in ("-i", "--Input"):
            input_file = cur_val
        elif cur_arg in ("-o", "--output"):
            output_file = cur_val
    
    # 1. Get all events from JSON file
    events = parse_json(input_file_path=input_file)
    # 2. Split branches and customers separately

    branches, customers = segregate_events(events)
    for c in customers:
        for e in c.events:
            log_data(logger=logger, message=f"Customer has ID: {c.id} has event {str(e)}")

    for b in branches:
        log_data(logger=logger, message=f"Branch has ID: {b.id} with balance {b.balance} the following branches {str(b.branches)}")

    log_data(
        logger=logger,
        message=f'==== Start process for branches===='
    )
    workers = []
    branch_address = []

    for branch in branches:
        branch_port = Allocate_Port()
        local_address = f"localhost:{branch_port}"

        worker = multiprocessing.Process(
            name=f'Branch-{branch.id}',
            target=Create_Branch,
            args=(branch, local_address, 5)
        )

        worker.start()
        workers.append(worker)
        branch_address.append([ branch.id, local_address])

        log_data(
            logger=logger,
            message=f"Started branch {worker.name} on initial balance {branch.amount}"
            f"with PID {worker.pid} at address {local_address} successfully."
        )

    log_data(
        logger=logger,
        message=f"=== Wait for {WAIT_TIME_IN_SECONDS} before starting other clients==="
    )

    time.sleep(WAIT_TIME_IN_SECONDS)

    log_data(
        logger=logger,
        message=f"=== Starting process for customers==="
    )


    for customer in customers:
        branch_addr = None
        for idx, [id, adr] in enumerate(branch_address):
            if customer.id == id:
                branch_addr = adr
                break
        
        worker = multiprocessing.Process(
            name=f"Customer-{customer.id}",
            target=Customer.create_customer_process,
            args={customer, branch_addr, output_file, THREAD_CONCURRENCY}
        )
        worker.start()
        workers.append(worker)

    for worker in workers:
        worker.join()

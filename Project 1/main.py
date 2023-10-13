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
THREAD_CONCURRENCY=2
WAIT_TIME_IN_SECONDS = 5

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
                events=transaction['events'],
                output_file=output_file
            )
            c.append(customer)
    branch_ids = {br.id: str(50000 + br.id) for br in b}
    for br in b:
        br.branches = branch_ids
        br.address = f"127.0.0.1:{str(50000 + br.id)}"

    return b, c

if __name__ == "__main__":
    argumentList = sys.argv[1:]

    # Options
    options = "hio"

    # Long options
    long_options = ["Help", "Input", "Output"]
    
    input_file = "input.json"
    output_file = "output.json"

    for idx_1, idx_2 in zip(range(0, len(argumentList), 2), range(1, len(argumentList), 2)):
        if argumentList[idx_1] in ("-h", "--Help"):
            log_data(
                logger=logger,
                message="Options:\n -i / --Input\t Input json file\n -o / -- Output\t Output json file")
        elif argumentList[idx_1] in ("-i", "--Input"):
            input_file = argumentList[idx_2]
        elif argumentList[idx_1] in ("-o", "--output"):
            output_file = argumentList[idx_2]
                
    
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
        local_address = branch.address

        worker = multiprocessing.Process(
            name=f'Branch-{branch.id}',
            target=Create_Branch,
            args=(branch, local_address)
        )

        worker.start()
        workers.append(worker)
        branch_address.append([ branch.id, local_address])

        log_data(
            logger=logger,
            message=f"Started branch {worker.name} on initial balance {branch.balance}"
            f" with PID {worker.pid} at address {local_address} successfully."
        )

    log_data(
        logger=logger,
        message=f"=== Wait for {WAIT_TIME_IN_SECONDS} seconds before starting other clients==="
    )

    time.sleep(WAIT_TIME_IN_SECONDS)

    log_data(
        logger=logger,
        message=f"=== Starting process for customers==="
    )


    for customer in customers:
        branch_addr = None
        for [idx, adr] in branch_address:
            if customer.id == idx:
                branch_addr = adr
                break
        
        worker = multiprocessing.Process(
            name=f"Customer-{customer.id}",
            target=Customer.create_customer_process,
            args=(customer, branch_addr)
        )
        worker.start()
        worker.join()
        
        workers.append(worker)

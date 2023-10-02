import json
import os
import sys, getopt
from Branch import Branch
from Customer import Customer

from utils import config_logger, log_data

# Initiate logger
logger = config_logger("Main")

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
            

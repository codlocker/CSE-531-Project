import json
import os
import sys, getopt
import Branch
import Customer

def parse_json(input_file_path: str):
    with open(input_file_path) as f:
        events = json.load(f)

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
            print("Options:\n -i / --Input\t Input json file\n -o / -- Output\t Output json file")
        elif cur_arg in ("-i", "--Input"):
            input_file = cur_val
        elif cur_arg in ("-o", "--output"):
            output_file = cur_val
    
    # 1. Get all events from JSON file
    events = parse_json(input_file_path=input_file)

    print(events)

    branches, customers = segregate_events(events)

    # 2. Split branches and customers separately

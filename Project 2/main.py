import json
import multiprocessing
from time import sleep
from concurrent import futures
import sys

import grpc
import BankService2_pb2_grpc
from Branch import Branch
from Customer import Customer

OUTPUT_FILE = 'output.json'
BRANCH_OUTPUT_FILE = 'branch_output.json'
CUSTOMER_OUTPUT_FILE = 'customer_output.json'

def run_branch(branch: Branch):
    branch.create_stubs()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    BankService2_pb2_grpc.add_BankService2Servicer_to_server(branch, server=server)

    port = str(50000 + branch.id)
    server.add_insecure_port(f"127.0.0.1:{port}")
    print(f'Starting server for branch {branch.id} at 127.0.0.1:{port}')
    server.start()

    # Step 4: Collect events after the events have been generated
    sleep(0.5 * branch.id)
    res = json.load(open(BRANCH_OUTPUT_FILE))
    res.append(
        {
            'id': branch.id, 
            'type': 'branch', 
            'events': branch.output()
        })

    final_res = json.dumps(res, indent=4)
    with open(BRANCH_OUTPUT_FILE, 'w') as f:
        f.write(final_res)
    
    server.wait_for_termination()
    
def run_customer(customer: Customer):
    customer.create_stub()
    customer.execute_events()

    sleep(0.5 * customer.id)
    res = json.load(open(CUSTOMER_OUTPUT_FILE))
    res.append(
        {
            'id': customer.id, 
            'type': 'customer', 
            'events': customer.output()
        })
    
    final_res = json.dumps(res, indent=4)
    with open(CUSTOMER_OUTPUT_FILE, 'w') as f:
        f.write(final_res)

def create_process(processes):
    customers = []
    customer_processes =  []

    branches = []
    branch_processes = []
    branchIds = []

    for process in processes:
        if process['type'] == 'branch':
            branch = Branch(
                id=process['id'],
                balance=process['balance'],
                branches=branchIds
            )
            branches.append(branch)
            branchIds.append(branch.id)
        
        if process['type'] == 'customer':
            customer = Customer(id=process['id'], events=process['customer-requests'])
            customers.append(customer)
    
    # Create branch processes
    for branch in branches:
        branch_process = multiprocessing.Process(target=run_branch, args=(branch,))
        branch_processes.append(branch_process)
        branch_process.start()

    print(f'Sleep for {0.25} seconds after branch server creation')
    sleep(2)

    # Create Customer processes
    for customer in customers:
        customer_process = multiprocessing.Process(target=run_customer, args=(customer,))
        customer_processes.append(customer_process)
        customer_process.start()

    for cp in customer_processes:
        cp.join()

    sleep(1)
    
    for bp in branch_processes:
        bp.terminate()

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'input.json'

    try:
        input = json.load(open(input_file))

        with open(OUTPUT_FILE, 'w') as f:
            f.write('[]')

        with open(BRANCH_OUTPUT_FILE, 'w') as f:
            f.write('[]')

        with open(CUSTOMER_OUTPUT_FILE, 'w') as f:
            f.write('[]')

        create_process(input)
        
    except Exception as e:
        print(e)
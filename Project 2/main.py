import json
import multiprocessing
from time import sleep
from concurrent import futures
import sys

import grpc
import BankService2_pb2_grpc
from Branch import Branch
from Customer import Customer

def run_branch(branch: Branch):
    branch.create_stubs()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    BankService2_pb2_grpc.add_BankService2Servicer_to_server(branch, server=server)

    port = str(50000 + branch.id)
    server.add_insecure_port(f"127.0.0.1:{port}")
    print(f'Starting server for branch {branch.id} at 127.0.0.1:{port}')
    server.start()

    server.wait_for_termination()
    
def run_customer(customer: Customer):
    customer.create_stub()
    customer.execute_events()

    # sleep(0.5 * customer.id)
    # print(customer.output())

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

    print(f'Sleep for {2} seconds after branch server creation')
    sleep(2)

    # Create Customer processes
    for customer in customers:
        customer_process = multiprocessing.Process(target=run_customer, args=(customer,))
        customer_processes.append(customer_process)
        customer_process.start()


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'input.json'
    output_file = 'output.json'

    try:
        input = json.load(open(input_file))

        with open(output_file, 'w') as f:
            f.write('[]')

        create_process(input)
        
    except Exception as e:
        print(e)
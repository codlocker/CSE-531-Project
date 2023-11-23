import json
import multiprocessing
from time import sleep
from concurrent import futures
import sys

import grpc
import BankService3_pb2_grpc
from Branch import Branch
from Customer import Customer

OUTPUT_FILE = 'output.json'
final_output = []

# Run branch process to create GRPC server.
# Args:
#     branch (Branch): Branch instance
def run_branch(branch: Branch):
    branch.create_stubs()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    BankService3_pb2_grpc.add_BankService3Servicer_to_server(branch, server=server)

    port = str(50000 + branch.id)
    server.add_insecure_port(f"127.0.0.1:{port}")
    print(f'Starting server for branch {branch.id} at 127.0.0.1:{port}')
    server.start()
    server.wait_for_termination()

# Run Customer branch to create customer processes.
# Args:
#     customer (Customer): Customer instance.
def run_customer(customer: Customer):
    customer.create_stub()
    customer.execute_events()

# Create process from all events
#    Args:
#        processes (list): list of processes of type branch and customer.
def create_process(processes: list):
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
            customer = Customer(id=process['id'], events=process['events'])
            customers.append(customer)
    
    # Create branch processes
    for branch in branches:
        branch_process = multiprocessing.Process(target=run_branch, args=(branch,))
        branch_processes.append(branch_process)
        branch_process.start()

    # Create Customer processes
    for customer in customers:
        customer_process = multiprocessing.Process(target=run_customer, args=(customer,))
        customer_processes.append(customer_process)
        customer_process.start()
        # sleep(0.1)

    for cp in customer_processes:
        cp.join()

    
    for bp in branch_processes:
        bp.terminate()

    final_output = json.load(open(OUTPUT_FILE))
    for customer in customers:
        final_output.append({
            'id': customer.id,
            'recv': list(customer.messages)
        })
    final_res = json.dumps(final_output, indent=2)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(final_res)
        

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'input.json'

    try:
        input = json.load(open(input_file))

        with open(OUTPUT_FILE, 'w') as f:
            f.write('[]')

        create_process(input)

        
    except Exception as e:
        print(e)
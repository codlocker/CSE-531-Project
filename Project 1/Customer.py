from concurrent import futures
import grpc
import time

import BankService_pb2
import BankService_pb2_grpc
from utils import config_logger, log_data, INTERFACE, RESPONSE_STATUS

cust_logger = config_logger("Customer")

class Customer:
    THREADS=5
    def __init__(self, id, events):
        # unique ID of the Customer
        self.id = id
        # events from the input
        self.events = events
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # pointer for the stub
        self.stub = None

    # TODO: students are expected to create the Customer stub
    def createStub(self, address: str):
        log_data(
            logger=cust_logger,
            message=f"Creating a stub for customer to branch at {address}")
        self.stub = BankService_pb2_grpc.MessageStub(grpc.insecure_channel(address))

        client = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.THREADS)
        )

        client.start()

    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        record = {'id': self.id, 'recv': []}
        for event in self.events:
            request_id = event['id']
            request_op = INTERFACE[event['interface']]
            request_val = event['money']
            response = self.stub.MsgDelivery(
                BankService_pb2.MsgDeliveryRequest(
                    s_id=request_id,
                    d_id=self.id,
                    interface=request_op,
                    amount=request_val
                )
            )

            log_data(
                logger=cust_logger,
                message=f'Response returned has status: {response.responseStatus} with money: {response.amount}')
            
            res = {
                'interface': event['interface'],
                'result': RESPONSE_STATUS[response['responseStatus']]
            }

            if request_op == BankService_pb2.QUERY:
                res['money'] = response.amount

            record['recv'].append(res)

        return record
    
    def create_customer_process(self, cust_pid, branch_pid):
        log_data(
            logger=cust_logger,
            message=f"Running client customer #{self.id} connecting to server {branch_pid}..."
        )

        Customer.create_customer_process(
            self,
            branch_pid
        )

        Customer.executeEvents(self)
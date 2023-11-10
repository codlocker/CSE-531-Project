from concurrent import futures
from multiprocessing import Manager, Lock
import grpc
import BankService2_pb2
import BankService2_pb2_grpc

class Branch(BankService2_pb2_grpc.BankService2Servicer):
    def __init__(self, id, balance, branches) -> None:
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stubList = list()
        self.events = Manager().list()
        self.clock = 1
        self.lock = Lock()

    def create_stubs(self):
        for bId in self.branches:
            if bId != self.id:
                port = str(50000 + bId)
                channel = grpc.insecure_channel(f"localhost:{port}")
                print(f"Creating a stub for branch #{bId} to branch at localhost:{port}")
                self.stubList.append((bId, BankService2_pb2_grpc.BankService2Stub(channel=channel)))
    
    def MsgDelivery(self, request, context):
        return self.process_message(request, False)
    
    def MsgPropagation(self, request, context):
        return self.process_message(request, True)
    
    def process_message(self, request, is_propagated):
        if not is_propagated:
            self.cust_request_recv(request)
        else:
            self.branch_request_recv(request)
            
        res = "success"

        if request.amount < 0:
            res = "fail"
        elif request.interface == "deposit":
            self.balance += request.amount
        elif request.interface == "withdraw":
            if self.balance >= request.amount:
                self.balance -= request.amount
            else:
                res = "fail"
        else:
            res = "fail"

        response = BankService2_pb2.MsgResponse(
            id=request.id,
            interface=request.interface,
            response=res,
            amount=self.balance,
            clock=self.clock,
            customer_request_id=request.customer_request_id
        )

        if not is_propagated:
            self.propagate_transaction(request)

        return response
    
    def propagate_transaction(self, request):
        for bId, stub in self.stubList:
            self.branch_request_sent(bId, request)

            response = stub.MsgPropagation(
                BankService2_pb2.MsgRequest(
                    # id=request.id
                    id=bId,
                    customer_request_id=request.customer_request_id,
                    interface=request.interface,
                    amount=request.amount,
                    clock=self.clock
                )
            )

    ##########################################
    # Methods for adding events to branches. #
    ##########################################

    def cust_request_recv(self, request):
        self.lock.acquire()
        try:
            self.clock = max(self.clock, request.clock) + 1
            print(f'Clock : {self.clock} Branch {self.id} receives Customer Request ID: {request.customer_request_id}')
            self.events.append(
                {
                    'customer-request-id': request.customer_request_id,
                    'logical_clock': self.clock,
                    'interface': request.interface,
                    'comment': f'event_recv from customer {request.id}'
                }
            )
        finally:
            self.lock.release()

    def branch_request_recv(self, request):
        self.lock.acquire()
        try:
            self.clock = max(self.clock, request.clock) + 1
            print(f'Clock : {self.clock} Branch {self.id} receives Branch propagate request for ID: {request.customer_request_id}')
            self.events.append(
                {
                    'customer-request-id': request.customer_request_id,
                    'logical_clock': self.clock,
                    'interface': f'propagate_{request.interface}',
                    'comment': f'event_recv from branch {request.id}'
                }
            )
        finally:
            self.lock.release()

    def branch_request_sent(self, bId, request):
        self.lock.acquire()
        try:
            self.clock += 1
            print(f'Clock : {self.clock} Branch {self.id} sends Branch propagate request for ID: {request.customer_request_id} to {bId}')
            self.events.append(
                {
                    'customer-request-id': request.customer_request_id,
                    'logical_clock': self.clock,
                    'interface': f'propagate_{request.interface}',
                    'comment': f'event_sent to branch {bId}'
                }
            )
        finally:
            self.lock.release()
    #####################################
    # Return the events stored by branch#
    #####################################
    def output(self):
        return list(self.events)
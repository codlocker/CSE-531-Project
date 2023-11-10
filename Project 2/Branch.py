from concurrent import futures
from multiprocessing import Manager, Lock
import grpc
import BankService2_pb2
import BankService2_pb2_grpc

class Branch(BankService2_pb2_grpc.BankService2Servicer):
    
    # Initializes a constructor for Branch
    #    Args:
    #        id (int): Branch id
    #        balance (float): Balance in the branch
    #        branches (list): set of branches that this communicates with.
    def __init__(self, id: int, balance: float, branches: list) -> None:
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stubList = list()
        self.events = Manager().list()
        self.clock = 1
        self.lock = Lock()

    # Create stuns for branch.
    def create_stubs(self):
        for bId in self.branches:
            if bId != self.id:
                port = str(50000 + bId)
                channel = grpc.insecure_channel(f"localhost:{port}")
                print(f"Creating a stub for branch #{bId} to branch at localhost:{port}")
                self.stubList.append((bId, BankService2_pb2_grpc.BankService2Stub(channel=channel)))
    
    #  Delivery message RPC call
    #    Args:
    #        request (_type_): Request type for Message
    #        context (_type_): Some data

    #    Returns:
    #        _type_: Response for Message sent.
    def MsgDelivery(self, request: BankService2_pb2.MsgRequest, context: any) -> BankService2_pb2.MsgResponse:
        return self.process_message(request, False)
    
    #  Propagation message RPC call
    #    Args:
    #        request (_type_): Request type for Message
    #        context (_type_): Some data

    #    Returns:
    #        _type_: Response for Message sent.
    def MsgPropagation(self, request, context):
        return self.process_message(request, True)
    
    # Process events of customer to branch or branch to branch requests.
    #    Args:
    #        request (BankService2_pb2.MsgRequest): Msg Request for contact
    #        is_propagated (bool): check if the request is from a customer or branch.

    #    Returns:
    #        BankService2_pb2.MsgResponse: Msg Response
    def process_message(self, request: BankService2_pb2.MsgRequest, is_propagated: bool) -> BankService2_pb2.MsgResponse:
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
    
    # Propagate request to other branches

    #    Args:
    #        request (BankService2_pb2.MsgResponse): Msg Request coming from branch
    
    def propagate_transaction(self, request: BankService2_pb2.MsgResponse):
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
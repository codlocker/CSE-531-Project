import grpc
from multiprocessing import Lock
import BankService3_pb2_grpc as bs3_grpc
from BankService3_pb2 import MsgRequest, MsgResponse

class Branch(bs3_grpc.BankService3Servicer):
    # Initializes the constructor for Branch.
    # Args:
    #    id (int): Branch ID.
    #    balance (int): Branch balance.
    #    branches (list): List of branches.
    #    src_port (int): Port start address
    def __init__(self, id: int, balance: int, branches: list, src_port: int) -> None:
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stub_list = []
        self.write_set = []
        self.lock = Lock()
        self.addr = src_port

    # Creates stubs for branches to connect to other branches.
    def create_stubs(self):
        print(f"Creating stubs for Branch : {self.id}")
        for b_id in self.branches:
            if b_id != self.id:
                port = str(self.addr + b_id)
                channel = grpc.insecure_channel(f"127.0.0.1:{port}")
                print(f"Creating branch stub for #{b_id} to branch at channel 127.0.0.1:{port}")
                self.stub_list.append((b_id, bs3_grpc.BankService3Stub(channel=channel)))
    
    # Add to the write-set if there is a new write.
    def add_new_write(self):
        new_event = len(self.write_set) + 1
        self.write_set.append(new_event)

    # Verify given writeset.
    #    Args:
    #       writeset (list): List of writesets.
    #    Returns:
    #        bool: Returns if request and branch writeset are the same since we need to correct the writes.
    def verify_writeset(self, writeset: list) -> bool:
        return set(writeset).issubset(set(self.write_set))
    
    # Deliver the message.
    #    Args:
    #        request (MsgRequest): Message request.
    #        context (any): Context of response.

    #    Returns:
    #        MsgResponse: return the response object.
    def MsgDelivery(self, request: MsgRequest, context) -> MsgResponse:
        print(f"Branch #{self.id} receives event from customer #{request.id} with interface={request.interface},"
                + f" amount={request.money}")        
        if self.verify_writeset(request.writeset):
            return self.process_msg(request, False)

    # Propagate the message from branch
    #    Args:
    #        request (MsgRequest): Request the propagation.
    #        context (any): Context object

    #    Returns:
    #        MsgResponse: Response of the message.
    
    def MsgPropagation(self, request: MsgRequest, context) -> MsgResponse:
        print(f"Branch #{self.id} receives prop event from branch #{request.branch} with interface={request.interface},"
                + f" amount={request.money}")
        if self.verify_writeset(request.writeset):
            return self.process_msg(request, True)
    
    # Process event messages.
    #    Args:
    #        request (MsgRequest): request
    #        is_propagated (bool): Verify if the message is from the customer or a branch

    #    Returns:
    #        _type_: Response object.
    def process_msg(self, request: MsgRequest, is_propagated: bool):
        res = "success"
        if request.interface == "query":
            pass
        elif request.interface == "deposit":
            self.balance += request.money
        elif request.interface == "withdraw":
            if self.balance >= request.money:
                self.balance -= request.money
            else:
                res = "failure"
        
        if request.interface != "query":
            # Add new event to the writeset
            self.add_new_write()

            if not is_propagated:
                self.propagate_request(request)
        
        return MsgResponse(
            id=request.id, 
            interface=request.interface,
            response=res,
            money=self.balance, 
            writeset=self.write_set)

    # Propagate request to other branches
    #    Args:
    #        request (MsgRequest): Message request propagate to other branches.
    def propagate_request(self, request: MsgRequest):
        self.lock.acquire()
        try:
            for b_id, stub in self.stub_list:
                stub.MsgPropagation(MsgRequest(
                    id=request.id,
                    interface=request.interface,
                    money=request.money,
                    branch=self.id,
                    writeset=request.writeset))
        finally:
            self.lock.release()

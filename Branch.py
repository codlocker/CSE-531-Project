import grpc
import multiprocessing
from concurrent import futures

import utils
import BankService_pb2
import BankService_pb2_grpc

logger = utils.config_logger('Branch')

class Branch(BankService_pb2_grpc.MessageServicer):
    THREADS = 5
    def __init__(self, id, balance, branches):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # iterate the processID of the branches
        # TODO: students are expected to store the processID of the branches
        self.processID = ''
        pass

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self, request, context):
        self.recvMsg.append(request)
        balance = None
        if request.interface == BankService_pb2.QUERY:
            balance = self.Query()
        elif request.interface == BankService_pb2.DEPOSIT:
            balance = self.Deposit(request.amount)

    def Query(self):
        return self.balance
    
    def Deposit(self, d_amount):
        if d_amount <= 0:
            return BankService_pb2.ERROR
        
        self.balance += d_amount
        return self.balance
    
    def Propagate_Deposit(self, request_id, amount):
        if not self.stubList:
            self.Create_StubList()
        for stub in self.stubList:
            response = stub.MsgDelivery(
                BankService_pb2.MsgDeliveryRequest(
                    s_id=request_id,
                    d_id=-1,
                    interface=BankService_pb2.DEPOSIT,
                    amount=amount
                )
            )

            utils.log_data(
                logger=logger,
                message=f'Send request to Branch : {request_id} from Branch : {self.id}.'
                f'Operation {utils.INTERFACE_MAP[BankService_pb2.DEPOSIT]} returns {utils.RESPONSE_STATUS[response.responseStatus]}'
                f'money {response.amount}'
            )

    def Withdraw(self, w_amount):
        if w_amount <= 0:
            return BankService_pb2.ERROR
        
        if self.balance - w_amount < 0:
            return BankService_pb2.FAILURE
        
        self.balance -= w_amount

        return BankService_pb2.SUCCESS, self.balance

    def Propagate_Withdraw(self, request_id, amount):
        if not self.stubList:
            self.Create_StubList()
        for stub in self.stubList:
            response = stub.MsgDelivery(
                BankService_pb2.MsgDeliveryRequest(
                    s_id=request_id,
                    d_id=-1,
                    interface=BankService_pb2.WITHDRAW,
                    amount=amount
                )
            )

            utils.log_data(
                logger=logger,
                message=f'Send request to Branch : {request_id} from Branch : {self.id}.'
                f'Operation {utils.INTERFACE_MAP[BankService_pb2.WITHDRAW]} returns {utils.RESPONSE_STATUS[response.responseStatus]}'
                f'money {response.amount}'
            )

    def Create_StubList(self):
        if len(self.stubList) == len(self.branches):
            return
        for b in self.branches:
            if b != self.id:
                process_id = self.processID
                utils.log_data(
                    logger=logger,
                    message=f'Initializing branch to branch stub at {process_id}'
                )
                self.stubList.append(BankService_pb2_grpc.BankServiceStub(
                    grpc.insecure_channel(process_id)
                ))


# Create a branch server

def Create_Branch(branch : Branch, processID):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=branch.THREADS,),
        options=('grpc.so_reuseport', 1))
    
    branch.processID = processID
    BankService_pb2_grpc.add_BankServiceServicer_to_server(branch, server)

    server.add_insecure_port(processID)
    server.start()
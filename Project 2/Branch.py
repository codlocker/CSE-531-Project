import grpc
import multiprocessing
from concurrent import futures
import time

import utils
import BankService2_pb2
import BankService2_pb2_grpc
from utils import config_logger, log_data, INTERFACE_MAP, RESPONSE_STATUS

logger = utils.config_logger('Branch')

class Branch(BankService2_pb2_grpc.BankService2Servicer):
    THREADS = 2 # A const determining number of threads

    # Initialize the constructor
    def __init__(self, id, balance, branches, branch_logger):
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
        self.address = ''
        # Initiate the clock
        self.clock = 0
        # Branch activity monitoring
        self.branch_logger = branch_logger

    # Update the msg delivery mechanism in relation to proto
    # This funciton proceses the request from customer and runs the
    # branch to branch communication.
    def MsgDelivery(self, request, context):
        self.recvMsg.append(request)
        balance = None
        resp_code = BankService2_pb2.SUCCESS

        if request.d_id != -1:
            self.event_request(
                clock=request.clock,
                interface=request.interface,
                id=request.s_id
            )
        else:
            self.propagate_request(
                clock=request.clock,
                interface=f'propagate_{request.interface}',
                id=request.s_id
            )
        
        if request.interface == BankService2_pb2.QUERY:
            balance = self.Query()
        elif request.interface == BankService2_pb2.DEPOSIT:
            balance = self.Deposit(request.amount)
        elif request.interface == BankService2_pb2.WITHDRAW:
            resp_code, balance = self.Withdraw(request.amount)
        
        log_data(
            logger=logger,
            message=f"Branch : {self.id} to event: {request.s_id} response: {RESPONSE_STATUS[resp_code]}"
             + f" Op: {INTERFACE_MAP[request.interface]} balance : {balance}"
        )

        response = BankService2_pb2.MsgResponse(
            id=request.s_id,
            responseStatus=resp_code,
            amount=balance,
            clock=self.clock)
        
        if request.d_id != -1 and request.interface == BankService2_pb2.DEPOSIT:
            self.Propagate_Deposit(
                request_id=request.d_id,
                amount=request.amount,
                request_clock=request.clock)
        if request.d_id != -1 and request.interface == BankService2_pb2.WITHDRAW and resp_code == BankService2_pb2.SUCCESS:
            self.Propagate_Withdraw(
                request_id=request.d_id,
                amount=request.amount,
                request_clock=request.clock
            )

        return response

    # Query the balance in the current bank proces
    def Query(self):
        return self.balance
    
    # Perform the deposit function to the account
    def Deposit(self, d_amount):
        if d_amount <= 0:
            return BankService2_pb2.ERROR
        
        self.balance += d_amount
        return self.balance
    
    # Propagate the deposit transaction to the rest of the branches
    def Propagate_Deposit(self, request_id, amount, request_clock):
        if not self.stubList:
            self.Create_StubList()
        for stub in self.stubList:
            self.event_sent(
                id=self.id,
                interface='deposit',
                clock=request_clock,
            )
            response = stub.MsgDelivery(
                BankService2_pb2.MsgRequest(
                    s_id=request_id,
                    d_id=-1,
                    interface=BankService2_pb2.DEPOSIT,
                    amount=amount
                )
            )

            utils.log_data(
                logger=logger,
                message=f'Send request to Branch : {request_id} from Branch : {self.id}.'
                f'Operation {utils.INTERFACE_MAP[BankService2_pb2.DEPOSIT]} returns {utils.RESPONSE_STATUS[response.responseStatus]}'
                f' money {response.amount}'
            )

    # Perform the withdraw function of the amount.
    def Withdraw(self, w_amount):
        if w_amount <= 0:
            return BankService2_pb2.ERROR
        
        if self.balance - w_amount < 0:
            return BankService2_pb2.FAILURE
        
        self.balance -= w_amount

        return BankService2_pb2.SUCCESS, self.balance

    # Propagate the withdraw action to the rest of the branches.
    def Propagate_Withdraw(self, request_id, amount, request_clock):
        if not self.stubList:
            self.Create_StubList()
        for stub in self.stubList:
            self.event_sent(
                id=self.id,
                interface='withdraw',
                clock=request_clock
            )

            response = stub.MsgDelivery(
                BankService2_pb2.MsgRequest(
                    s_id=request_id,
                    d_id=-1,
                    interface=BankService2_pb2.WITHDRAW,
                    amount=amount
                )
            )

            utils.log_data(
                logger=logger,
                message=f'Send request to Branch : {request_id} from Branch : {self.id}.'
                f'Operation {utils.INTERFACE_MAP[BankService2_pb2.WITHDRAW]} returns {utils.RESPONSE_STATUS[response.responseStatus]}'
                f'money {response.amount}'
            )

    # Creates the stub list for branch ot branch communication
    def Create_StubList(self):
        if len(self.stubList) == len(self.branches):
            return
        for b in self.branches:
            if b != self.id:
                process_id = f"localhost:{self.branches[b]}"
                utils.log_data(
                    logger=logger,
                    message=f'Initializing branch to branch stub at {process_id}'
                )
                self.stubList.append(BankService2_pb2_grpc.BankService2Stub(
                    grpc.insecure_channel(process_id)
                ))

    ###################################
    # Clock related functionalities   #
    ###################################

    def event_request(self, id: int, interface: str, clock: int):
        self.clock = max(self.clock, clock) + 1
        self.add_branch_log({
            "customer-request-id": id,
            "interface": interface,
            "logical_clock": clock,
            "comment": f"event_recv from customer {id}" 
        })

    def event_sent(self, id: int, interface: str, clock: int):
        self.clock = max(self.clock, clock) + 1
        self.add_branch_log({
            "customer-request-id": id,
            "interface": interface,
            "logical_clock": clock,
            "comment": f"event_sent to branch {id}" 
        })

    def propagate_request(self, id: int, interface: str, clock: int):
        self.clock = max(self.clock, clock) + 1
        self.add_branch_log({
            "customer-request-id": id,
            "interface": interface,
            "logical_clock": clock,
            "comment": f"event_recv from branch {id}" 
        })
    ####################################################
    # Event / Branch Logging related functionalities   #
    ####################################################

    def add_branch_log(self, log):
        if self.id not in self.branch_logger:
            self.branch_logger[self.id] = [log]
        else:
            self.branch_logger[self.id].append(log)
    
# Create a branch server
def Create_Branch(branch : Branch, processID: str):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=branch.THREADS,),
        options=(('grpc.so_reuseport', 1),))
    
    branch.address = processID
    BankService2_pb2_grpc.add_BankService2Servicer_to_server(branch, server)

    server.add_insecure_port(processID)
    server.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(None)
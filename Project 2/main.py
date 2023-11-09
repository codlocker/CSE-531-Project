from concurrent import futures

import grpc
import BankService2_pb2
import BankService2_pb2_grpc

class Branch(BankService2_pb2_grpc.BankService2Servicer):
    def __init__(self, id, balance, branches) -> None:
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stubList = list()
        self.events = list()
        self.clock = 1

        
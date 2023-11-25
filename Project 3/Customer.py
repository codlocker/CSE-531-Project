import grpc
from multiprocessing import Manager
import BankService3_pb2_grpc
from BankService3_pb2 import MsgRequest

class Customer:
    # Initializes a constructor.
    # Args:
    #   id (int): Branch ID.
    #   events (list): List of events.
    #   src_port (int): Port start address
    def __init__(self, id: int, events: list, src_port: int) -> None:
        self.id = id
        self.events = events
        self.messages = Manager().list()
        self.writeset = []
        self.addr = src_port

    # Create stubs for customers.
    def create_stub(self):
        port = str(self.addr + self.id)
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")

        print(f"Creating a stub for customer #{self.id} to branch at localhost:{port}")
        self.stub = BankService3_pb2_grpc.BankService3Stub(channel=channel)

    # Execute events sent by customer.
    def execute_events(self):
        for event in self.events:
            if event['interface'] != 'query':
                print(f"Customer #{self.id} sends event ID #{event['id']} with interface={event['interface']},"
                    + f" amount={event['money']} to branch {event['branch']}")
            else:
                print(f"Customer #{self.id} sends event #{event['id']} with interface={event['interface']},"
                    + f"to branch {event['branch']}")
            
            port = str(self.addr + event['branch'])
            channel = grpc.insecure_channel(f'127.0.0.1:{port}')
            stub = BankService3_pb2_grpc.BankService3Stub(channel=channel)

            result = stub.MsgDelivery(
                MsgRequest(
                    id=self.id,
                    interface=event['interface'],
                    money=int(event['money'] if 'money' in event else 0),
                    branch=event['branch'],
                    writeset=self.writeset
                )
            )

            if result.interface != 'query':
                self.messages.append({
                    'interface': result.interface,
                    'branch': event['branch'],
                    'result': result.response
                })
            else:
                self.messages.append({
                    'interface': result.interface,
                    'branch': event['branch'],
                    'balance': result.money
                })

            print(f"Resposne obtained: interface {result.interface} balance {result.money} status {result.response}")
            if event['interface'] != 'query':
                self.writeset = result.writeset
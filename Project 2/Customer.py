import grpc
import BankService2_pb2
import BankService2_pb2_grpc

class Customer:
    def __init__(self, id, events) -> None:
        self.id = id
        self.events = events
        self.cust_events = list()
        self.stub = None
        self.clock = 1


    def create_stub(self):
        port = str(50000 + self.id)
        channel = grpc.insecure_channel(f"localhost:{port}")

        print(f"Creating a stub for customer #{self.id} to branch at localhost:{port}")
        self.stub = BankService2_pb2_grpc.BankService2Stub(channel=channel)

    def execute_events(self):
        for event in self.events:
            print(f'Clock : {self.clock} Customer {self.id} sending event {event["customer-request-id"]} to branch {self.id} => Event: {event["interface"]}'
                   + f'Money: {event["money"]} ')
            self.cust_events.append({
                'customer-request-id': event['customer-request-id'],
                'logical_clock': self.clock,
                'interface': event['interface'],
                'comment': f'event_sent from customer {self.id}'
            })

            response = self.stub.MsgDelivery(
                BankService2_pb2.MsgRequest(
                    id=self.id,
                    interface=event['interface'],
                    amount=event['money'],
                    clock=self.clock,
                    customer_request_id=event['customer-request-id']
                )
            )

            self.clock += 1

    def output(self):
        return self.cust_events
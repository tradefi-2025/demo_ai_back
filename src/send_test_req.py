import pika
import json
import uuid


def handle( ch, method, props, body):
    print(props.correlation_id )
    print(body)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue
    channel.basic_consume(callback_queue,handle,auto_ack=True)
    corr_id = str(uuid.uuid4())

    channel.basic_publish(exchange='',
                      routing_key='rpc_queue',
                      properties=pika.BasicProperties(
                            reply_to = callback_queue,
                            correlation_id=corr_id,
                            ),
                      body=json.dumps({"message": "hello_world"}))
    channel.start_consuming()

if __name__=="__main__":
    main()
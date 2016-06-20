#####################################################################
# File: messagequeue.py
# Author: Jeremy Mwenda <jmwenda@bu.edu>
# Desc: Class MessageQueue is used for sending and receiving messages
# from RMQ. An instance of this class should only be used for either
# sending or receiving, not both.
# TODO: add hostname and queue name to config file
# TODO: handle RMQ exceptions
#
# Dependencies:
# rabbitmq-server
# pika -- pip install pika 
#
#####################################################################

import pika
import json
import os
import subprocess as sub
import string
import logging

from lib.sdhash import exec_cmd, valid_hash, compare_hashes
logger = logging.getLogger(__name__)

class MessageQueue:
    def __init__(self, host, queue, elasticDB):
        self.host = host
        self.queue = queue
        self.conn = self.__get_connection(self.host)
        self.channel = self.conn.channel()
        self.channel.queue_declare(queue=queue) # create/ensure queue exists
        self.es = elasticDB

    def __get_connection(self, host):
        return pika.BlockingConnection(pika.ConnectionParameters(host))

    # send message using default exchange 
    def send(self, message):
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   body=message)
        #print 'Done sending: ', message

    # declare a callback to process received message
    def callback(self, ch, method, properties, body):
        data = json.loads(body)
        image = data['image']
        base_image = data['base_image']
        file_path = data['relative_path']
        operation = data['operation']
        sdhash = data['sdhash']
        file = data['file_path']

        # We always store only the base images for reference
        if operation == "store":
            basename = file_path.split('/')[-1]
            body = {'file': file_path,
                    'sdhash': sdhash,
                    'basename': basename}
            self.es.index(index=base_image, filename=file_path, body=body)
        else:
            if not valid_hash(sdhash):
                return

            fileDict = self.es.search(index=base_image, filename=file_path)
            if fileDict == None:
                logger.debug("skip file as its not present")
                return

            ref_sdhash = fileDict['_source']['sdhash']
            score = compare_hashes(sdhash, ref_sdhash)
            if score == "100":
                logger.debug(file + ' match 100%')
            else:
                try:
                    file_path = string.replace(file_path, ':', '_')
                    clamresult = sub.check_output(['clamscan',
                                                   file_path,
                                                   '--no-summary'],
                                                  stderr=sub.STDOUT)
                    logger.debug("clamscan's result: %s, file: %s" %
                                 (clamresult, file_path))
                except sub.CalledProcessError as ex:
                    logger.error("returncode other than 0 for ", file_path)
                    clamresult = ex.output
                judgeIndex = 'judgeresult:' + image
                # TODO if use index_file, here the body will
                # be {'sdhash': resline}.  Better change the key
                basename = file.split('/')[-1]
                body = {'file': file,
                        'sdhash': sdhash,
                        'basename': basename,
                        'safe': False,
                        'clamscan-result': clamresult}
                self.es.index(index=judgeIndex, filename=file, body=body)

    # continuously process messages
    def start_consuming(self):
        self.channel.basic_consume(self.callback,
                                   queue=self.queue,
                                   no_ack=True)
        print('Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    # close connection when done
    def close(self):
        self.conn.close()

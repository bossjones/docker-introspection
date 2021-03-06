## RabbitMQ
**RabbitMQ** is used for channelling messages from a producer process to a consumer process.
When endpoint.py receives notification of an image push, it calculates sdhashes of the image files and queues them into RMQ.
processor.py is the consumer process which receives messages (sdhashes) from RMQ and indexes or does lookups in elasticsearch.

### Installing RabbitMQ
(Detailed instructions can be found at https://www.rabbitmq.com/install-debian.html)

Add the following line to your `/etc/apt/sources.list`:

`deb http://www.rabbitmq.com/debian/ testing main`

(Please note that the word testing in this line refers to the state of our release of RabbitMQ, not any particular Debian distribution. You can use it with Debian stable, testing or unstable, as well as with Ubuntu. We describe the release as "testing" to emphasise that we release somewhat frequently.)

Then run:
```
$ sudo apt-get update
$ sudo apt-get install rabbitmq-server
```

### Running the server:
The server is started as a daemon by default when the RabbitMQ server package is installed.
As an administrator, start and stop the server as usual for Debian/Ubuntu using:
`invoke-rc.d rabbitmq-server stop/start/etc`.

**Install python rabbitMQ library:** 
`$ pip install pika`

### Putting everything together:
Run `python endpoint.py` to start listening for pushed images.
In another terminal, run `python processor.py` to process messages from RMQ.
Do an image push to test that the image is detected and processed.

### Other useful commands:
Clearing a queue: `$ sudo rabbitmqctl purge_queue queuename`

List queues, show message count:
`$ sudo rabbitmqctl list_queues`

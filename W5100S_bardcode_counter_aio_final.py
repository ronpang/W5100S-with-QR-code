import board
import busio
import digitalio
import analogio
import time
from random import randint
from secrets import secrets
import adafruit_sht31d

from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

from adafruit_io.adafruit_io import IO_MQTT
import adafruit_minimqtt.adafruit_minimqtt as MQTT

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

#set the internet button for the QR code reader
button = digitalio.DigitalInOut(board.GP2)
button.direction = digitalio.Direction.OUTPUT
button.value = 1
button.value = 0

#Counter method
pulses = digitalio.DigitalInOut(board.GP13)
pulses.direction = digitalio.Direction.INPUT

pulses2 = digitalio.DigitalInOut(board.GP12)
pulses2.direction = digitalio.Direction.INPUT

#Counter LED
LED = digitalio.DigitalInOut(board.GP11)
LED.direction = digitalio.Direction.OUTPUT

#QR code data input
RX0 = board.GP1
TX0 = board.GP0
uart = busio.UART(TX0, RX0, baudrate=9600, receiver_buffer_size=2048)
result = uart.readline()

#SPI
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

#Reset
W5x00_RSTn = board.GP20

print("Wiznet5k Adafruit Up&Down Link Test (DHCP)")
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 1, 100)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)


ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# For Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(SPI0_CSn)
# For Particle Ethernet FeatherWing
# cs = digitalio.DigitalInOut(board.D5)

spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

# Reset W5x00 first
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True

# # Initialize ethernet interface without DHCP
# eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
# # Set network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ ADDRESS, DNS_SERVER)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))


""" Counter section"""
class pulse_detect:
    counter = 0
    C_counter = 0
    T_counter = 0
    wait_count = 0
    #p_counter = 0
    current_stage = None
    previous_stage = 0b00
    flow = None
    flow2 = None
    direction = None
    def __init__(self, pulse,pulse2):
        self.pulse = pulse # Main on the left
        self.pulse2 = pulse2 # Direction support  - on the right

    def stage (self):
        """Two IR Sensor - Direction counting"""
        if self.pulse.value is False:
            self.flow = 0b00
        elif self.pulse.value is True:
            self.flow = 0b10
            #self.p_counter += 1
        if self.pulse2.value is False:
            self.flow2 = 0b00
        elif self.pulse2.value is True:
            self.flow2 = 0b01
        self.current_stage = self.flow +self.flow2

    def hole_count(self):
        """Two IR Sensor - Direction counting"""
        if self.previous_stage is 0b11 and self.current_stage is not self.previous_stage:
            if self.current_stage is 0b01:
                self.counter += 1
            elif self.current_stage is 0b10:
                self.counter -= 1
            self.wait_count = 0
        elif self.current_stage is self.previous_stage:
            self.wait_count += 1
            
        self.previous_stage = self.current_stage
        #print (self.counter)
        self.C_counter = round(self.counter /3)
                             
    def chip_count(self):
        R_data = 0
        wait = 0
        while True:
            wait = self.wait_count /10000
            if wait > 1:
                self.C_counter = 0
                self.counter = 0
                self.wait_count = 0
                return R_data
                    
            time.sleep(1/1000000000000)
            self.stage()
            self.hole_count()
            if R_data is not int(self.C_counter):
                R_data = int(self.C_counter)
                print ("Chip count: " + str(R_data))

#Activate the counter
detect = pulse_detect (pulses, pulses2)
message = None

### Topic Setup ###
# Adafruit IO-style Topic
# Use this topic if you'd like to connect to io.adafruit.com
# mqtt_topic = secrets["aio_username"] + '/feeds/test'

### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to Adafruit IO!")
    
    # Subscribe to Group
    io.subscribe(group_key=group_name)

def disconnected(client):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from Adafruit IO!")

def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))
    
def message(client, topic, message):
    # Method callled when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))
    
def control(client, topic, message):
    # Method callled when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))
    if message == "1":
        button.value = 1
    elif message == "0":
        button.value = 0
    else:
        print("Unexpected message on feed")
        
def LED_light(client, topic, message):
    # Method callled when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))
    if message == "1":
        LED.value = 1
    elif message == "0":
        LED.value = 0
    else:
        print("Unexpected message on feed")


# Initialize MQTT interface with the ethernet interface
MQTT.set_socket(socket, eth)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    is_ssl=False,
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Setup the callback methods above
io.on_connect = connected
io.on_disconnect = disconnected
io.on_message = message
io.on_subscribe = subscribe


# Set up a callback for the QR code control feed
io.add_feed_callback("testing.control", control)
io.add_feed_callback("testing.led", LED_light)

# Group name
group_name = "testing"

# Feeds within the group
result_feed = "testing.result"
counter_feed = "testing.counter"
LED_feed = "testing.led"

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# # Subscribe to all messages on the led feed
io.subscribe("testing.control")
io.subscribe("testing.led")
print("Connected to Adafruit !!")
while True:
    io.loop()
    result = uart.readline()
    print(result)
    if result != None:
        output = str(result.decode('utf-8')).split('\r')
        print(output[0])
        io.publish(result_feed, str(output[0]))
    
    if LED.value is True:
        print ("start counting")
        count = detect.chip_count()
        io.publish(counter_feed, str(count))
        io.publish(LED_feed, str(0))
        LED.value = 0
        
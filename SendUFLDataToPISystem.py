#Copyright 2016 OSIsoft, LLC
#
#Licensed under the Apache License, Version 2.0 (the "License")
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#<http:#www.apache.org/licenses/LICENSE-2.0>
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

# ************************************************************************
# Import packages
import sys, json, random, time, platform, requests, socket, datetime, linux_metrics, base64
from gps import *
import threading

# Specify the number of seconds to sleep in between value messages
number_of_seconds_between_value_messages = 5

# This name will be automatically populated (or you can hard-code it) this is the name
# of the PI AF Element that will be created, and it'll be included in the names
# of PI Points that get created as well
device_name = (socket.gethostname())+ ""

# ************************************************************************

# Specify the address of the destination endpoint
target_url = "https://4000vlecs1.cloudapp.net:5460/connectordata/dataFromDgB/"

# Specify the basic auth credentials needed to access this endpoint
_u = "iot-account";
_p = "student";

# If self-signed certificates are used (true by default), do not verify HTTPS SSL certificates
verify_SSL = False

# Suppress insecure HTTPS warnings, if an untrusted certificate is used by the target endpoint
if verify_SSL == False:
    requests.packages.urllib3.disable_warnings()
    
# ************************************************************************    
# Initialize the GPS polling class

# Initialize a global variable
gpsd = None 
class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd 
        gpsd = gps(mode=WATCH_ENABLE) 
        self.current_value = None
        self.running = True

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next()
        
# ************************************************************************

def sendDataValueMessage(dataFromDevice):
        try:  
                # Assemble headers
                msg_header = {"Authorization": ("Basic " + base64.b64encode(_u + ":" + _p)) }
                # Send the request, and collect the response
                response = requests.put(target_url, headers=msg_header, data=dataFromDevice, verify=verify_SSL, timeout=30)
                # Print a debug message, if desired
                print('Response from the message: {0} {1}'.format(response.status_code, response.text))
        except Exception as e:
                # Log any error, if it occurs
                print((str(datetime.datetime.now())) + " An error ocurred during web request: " + str(e))

# ************************************************************************

# Define the main program
if __name__ == '__main__':
    # Start the GPS polling thread
    gpsp = GpsPoller() 
    gpsp.start()

    # Loop indefinitely, sending events 
    print("--- Next sending live data every " + str(number_of_seconds_between_value_messages) + " second(s) for device " + device_name + "...")
    while (1):
        # Wait for the sensors to initialize
        time.sleep(0.01)
        
        # Get the current timestamp
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") 

        # Build a data object
        # Include metadata and all analog readings
        dataFromDevice = "DragonBoardData," + \
            timestamp + "," + \
            device_name + "," + \
            platform.machine() + "," + \
            platform.platform() + "," + \
            platform.processor() + "," + \
            str(100 - (linux_metrics.cpu_stat.cpu_percents(sample_duration=1))['idle']) + "," + \
            str(linux_metrics.disk_stat.disk_busy('mmcblk0', sample_duration=1)) + "," + \
            str(linux_metrics.mem_stat.mem_stats()[0]) + "," + \
            str(linux_metrics.mem_stat.mem_stats()[1]) + "," + \
            str(linux_metrics.net_stat.rx_tx_bits('wlan0')[0]) + "," + \
            str(linux_metrics.net_stat.rx_tx_bits('wlan0')[1]) + "," + \
            str(gpsd.fix.latitude) + "," + \
            str(gpsd.fix.longitude)
        
        # Send the message
        sendDataValueMessage(dataFromDevice)    
        
        # Wait until the next send
        time.sleep(number_of_seconds_between_value_messages)
    


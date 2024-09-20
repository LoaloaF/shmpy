import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM'))

import time
import logging
from threading import Thread

from CustomLogger import CustomLogger as Logger

# from process_launcher import open_camera2shm_proc
# from process_launcher import open_shm2cam_stream_proc
from SHM.shm_creation import create_cyclic_packages_shm
from SHM.shm_creation import create_singlebyte_shm

from SHM.FlagSHMInterface import FlagSHMInterface
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

from read2SHM.portenta2shm2portenta import run_portenta2shm2portenta
from read2SHM.portenta2shm2portenta_sim import run_portenta2shm2portenta_sim
from streamer.display_packages import run_stream_packages

# from process_launcher import open_por2shm2por_proc
# from process_launcher import open_log_portenta_proc
# from process_launcher import open_stream_portenta_proc
# from process_launcher import open_por2shm2por_sim_proc

# from streamer.display_camera import run_display_camera

ARDUINO_PORT = "/dev/usbmodem/"
ARDUINO_BAUD_RATE = 2_000_000
DATA_DIRECTORY = './data/'

def test_portenta2shm2portenta():
    L = Logger()
    
    # setup termination, triggered by input from here
    termflag_shm_struc_fname = create_singlebyte_shm(shm_name="termflag")
    # setup 
    ballvelocity_shm_struc_fname = create_cyclic_packages_shm(shm_name="BallVelCyclicTestSHM", 
                                                              package_nbytes=128, 
                                                              npackages=int(2**13)) # 8MB
    # setup 
    portentaoutput_shm_struc_fname = create_cyclic_packages_shm(shm_name="SensorEventsCyclicTestSHM", 
                                                              package_nbytes=128, 
                                                              npackages=int(2**13)) # 8MB
    # setup commands to Portenta, triggered by input from here
    portentainput_shm_struc_fname = create_cyclic_packages_shm(shm_name="CommandCyclicTestSHM", 
                                                               package_nbytes=32, 
                                                               npackages=8)
    
    portenta2shm_kwargs = {
        "termflag_shm_struc_fname": termflag_shm_struc_fname,
        "ballvelocity_shm_struc_fname": ballvelocity_shm_struc_fname,
        "portentaoutput_shm_struc_fname": portentaoutput_shm_struc_fname,
        "portentainput_shm_struc_fname": portentainput_shm_struc_fname,
        # uncomment when using real file without _sim.py
        "port_name": ARDUINO_PORT,
        "baud_rate": ARDUINO_BAUD_RATE,
        }
    
    stream_portenta_kwargs = portenta2shm_kwargs.copy()
    stream_portenta_kwargs.pop("portentainput_shm_struc_fname")
    stream_portenta_kwargs.pop("port_name", None)
    stream_portenta_kwargs.pop("baud_rate", None)

    L.spacer()
    Thread(target=run_portenta2shm2portenta, kwargs=portenta2shm_kwargs).start()
    # Thread(target=run_portenta2shm2portenta_sim, kwargs=portenta2shm_kwargs).start()
    #matplotlib GUI only runs on main Thread
    # Thread(target=run_stream_packages, kwargs=stream_portenta_kwargs).start()
    run_stream_packages(**stream_portenta_kwargs)
    
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    command_shm = CyclicPackagesSHMInterface(portentainput_shm_struc_fname)
    
    while True:
        t = time.time()
        if t-int(t) < 0.001:
            break
    try:
        i = 0
        while True:
            t1 = time.time()
            if t1 > t+i:
                command_shm.push("S100,100\r\n")
                L.logger.info("Pushed")
                i += 5
            
    except KeyboardInterrupt:
        L.spacer()
        termflag_shm.set()
        exit()

def main():
    ARDUINO_PORT = "/dev/ttyACM0"
    LOGGING_DIR = './logs'

    L = Logger()
    L.init_logger("__main__", LOGGING_DIR, "INFO")
    # L.spacer()
    L.logger.info("Testing Portenta/Sensors SHM read and write")
    test_portenta2shm2portenta()

if __name__ == "__main__":
    main()
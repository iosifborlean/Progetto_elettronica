import serial
import imufusion
import numpy as np


ahrs = imufusion.Ahrs()
scheda = serial.Serial('COM6', 115200, timeout=None)

a = np.array([2,3])
while True:
    line = scheda.read(55)
    scheda.reset_input_buffer()
    line = line.decode("utf")
    line = line.split("\n")[0]
    line = line.split(",")
    accelero = np.array([(float(line[0]) / 1000), (float(line[1]) / 1000), (float(line[2]) / 1000)])
    gyro = np.array([(float(line[3]) / 1000), (float(line[4]) / 1000), (float(line[5]) / 1000)])
    ahrs.update_no_magnetometer(gyro, accelero, 1 / 50)
    eulero = ahrs.quaternion.to_euler()
    if eulero[1] > 20 or eulero[1] < -20 :
        print("ciao")
    scheda.reset_input_buffer()

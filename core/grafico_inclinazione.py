import imufusion
import matplotlib.pyplot as plt
import numpy as np
import sys


data = np.genfromtxt("../../../AppData/Roaming/JetBrains/PyCharmCE2023.1/scratches/sensor_data.csv", delimiter=",", skip_header=1)

timestamp = data[0:1000, 0]

data = np.genfromtxt("../../../AppData/Roaming/JetBrains/PyCharmCE2023.1/scratches/dati.txt", delimiter=",")

gyroscope = data[:, 3:6]
accelerometer = data[:, 0:3]

_, axes = plt.subplots(nrows=3, sharex=True)

# Process sensor data
ahrs = imufusion.Ahrs()

euler = np.empty((len(timestamp), 3))

for index in range(len(timestamp)):
    ahrs.update_no_magnetometer(gyroscope[index], accelerometer[index], 1/50)  # 100 Hz sample rate
    euler[index] = ahrs.quaternion.to_euler()

# Plot Euler angles
axes[2].plot(timestamp, euler[:, 0], "tab:red", label="Roll")
axes[2].plot(timestamp, euler[:, 1], "tab:green", label="Pitch")
axes[2].plot(timestamp, euler[:, 2], "tab:blue", label="Yaw")
axes[2].set_title("Euler angles")
axes[2].set_xlabel("Seconds")
axes[2].set_ylabel("Degrees")
axes[2].grid()
axes[2].legend()

plt.show(block="no_block" not in sys.argv)  # don't block when script run by CI




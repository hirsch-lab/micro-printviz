# micro-printviz
Tool for plotting structured print messages from a microcontroller in real time



## Overview:



**Purpose**: When working with microcontrollers and physical systems like sensors, actuators, etc., it is often useful to visualize measurements or control signals in real-time. This project demonstrates how to plot data sent from a MicroPython device via print statements in real-time.



**Components**:

- A MicroPython device (like Raspberry Pi Pico) that runs a script (e.g., pico_demo.py).

- A host machine connected to the MicroPython device via USB that runs the plot_logs.py script.
  The connection between the MicroPython device and the host machine is established using mpremote.

- This tool comes with a bash script run.sh that runs the MicroPython script and the plot_logs.py script in parallel



The easiest way to visualize the print messages from a MicroPython script
with this tool is to run the script run.sh. 

```bash
./run.sh <script.py> [args-for-visualizer]

# Example 1: Run the script pico_demo.py and start
#            the visualizer with default settings
./run.sh pico_demo.py

# Example 2: Run the script pico_demo.py and start the
#            visualizer with custom settings: Set the
#            columns containing the x and y values, and 
#            set the maximum number of samples
./run.sh pico_demo.py --x-col 2 --y-col 3 --max-samples 300

# Example 3: Setting multiple x and y columns is also possible
./run.sh pico_demo.py --x-cols 0 2 --y-cols 1 3  
./run.sh pico_demo.py --x-col 0 --y-cols 1 2 3 
./run.sh pico_demo.py --x-col 0
```





![demo](./doc/demo.gif)







## Installation / Setup

To install the required packages:

```bash
pip install -r requirements.txt
```



## Detailed instructions

After installing the prerequisites, start a new terminal session and try to connect to the MicroPython device using mpremote.
Make sure that other applications that could use the serial port (such as Thonny, MicroPico extension...) are disabled.

```bash
# List available serial ports
mpremote connect list

# Run a script on the Pico device
mpremote run <path>
mpremote run pico_demo.py
```

The last command will generate output similar to the following

```
x(t), x_n(t), x_s(t)
1.106,1.604,1.053
1.223,1.599,1.138
1.348,1.459,1.244
1.482,1.565,1.363
1.623,1.158,1.493
1.769,1.917,1.631
1.916,2.134,1.774
2.062,1.770,1.918
2.202,2.383,2.060
2.334,2.038,2.197
...
```

 If this output is continuously forwarded into a text file, we can use the plot_logs.py script to visualize the data in real-time.

**Important**: The printed data must be formatted as comma-separated values (CSV), optionally with a header. The data will be parsed using the pandas library, and the plot will be generated using matplotlib.

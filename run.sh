#!/usr/bin/env bash

###############################################################################
# CHECK INPUT
###############################################################################

# Check if mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "mpremote is not installed. Please install it by running:"
    echo "pip install mpremote"
    exit 1
fi

# Check the number of arguments, and print usage:
# ./run.sh <script.py> [args-for-visualizer]
if [ "$#" -lt 1 ]; then
    echo "Usage: ./run.sh <script.py> [args-for-visualizer]"
    exit 1
fi

# Print help message if -h or --help is passed
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "###############################################################################"
    echo "Run a local script on the pico, and start the log visualizer at the same time."
    echo "Usage: ./run.sh <script.py> [args-for-visualizer]"
    echo "###############################################################################"
    echo 
    echo The arguments for the visualizer:
    python plot_logs.py --help
    exit 0
fi

# Get the script name
script=$1
# Check if file exists
if [ ! -f $script ]; then
    echo "File not found: $script"
    exit 1
fi

# Forward only the extra arguments to the script
shift

###############################################################################
# PREPARATIONS
###############################################################################
# Make sure to kill the visualizer when the script exits
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# Create a folder "logging", if it doesn't exist
mkdir -p "logging"

# Extract the basename of the script without extension
script_name=$(basename "$script" .py)
log_file="logging/log_$script_name.txt"

###############################################################################
# MAIN
###############################################################################
# Start the debugger/visualizer
echo "Starting the visualizer..."
# Forward additional arguments of this bash script to the python script
python plot_logs.py --file="$log_file" "$@" &

# Run the script on the pico
echo "Running $script on the pico..."
mpremote run "$script" | tee "$log_file"


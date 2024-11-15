"""
How to use this tool with your MicroPython code:

    - Use formatted print statements:
        - print("e(t), Ie(t), de(t), u(t)")
        - print("%.2f, %.2f, %.2f, %.2f" % (e, Ie, de, u))
    - Use comma separated values!
    - Use a header at the beginning
    - Don't use any additional formatting
    
Install mpremote on your client machine:
    - pip install mpremote
    - Usage:
        - mpremote --help           # Help
        - mpremote ls               # List the filesystem
        - mpremote connect list     # List available serial ports
        - mpremote run script.py    # Run a script on the board
    - For logging, use the following command:
        - mpremote run script.py | tee logging/log.txt
        
While running the MicroPython code using mpremote, run this script in a 
separate terminal or within an IDE. It will plot the data in real-time.
"""


import sys
import time
import argparse
import numpy as np
import pandas as pd
from io import StringIO
from pathlib import Path
from collections import deque
import matplotlib.pyplot as plt
from matplotlib import colors as mplc
from itertools import product, cycle


def load_configs(args):
    configs = dict()
    configs["path_to_logs"] = "logging/log.txt"
    configs["sleep_time"] = 0.05
    configs["max_samples"] = 100
    configs["timeout"] = 10  # seconds
    configs["columns"] = None
    configs["time"] = None
    configs["rescale_speed"] = 0.1   # Controls the rescaling (range: (0, 1])
    configs["lim_margin"] = 0.05     # Controls the margin of the x-/y-axis
    
    # Update configurations with command line arguments
    if args.file is not None:
        configs["path_to_logs"] = args.file
    if args.sleep is not None:
        configs["sleep_time"] = args.sleep
    if args.max_samples is not None:
        configs["max_samples"] = args.max_samples
    if args.timeout is not None:
        configs["timeout"] = args.timeout
    
    configs["x_cols"] = args.x_cols
    configs["y_cols"] = args.y_cols
            
    palette = ["#2D8FF3", "#FC585E", "#1AAF54"]
    # https://mycolor.space / 3-color-gradient
    palette = ["#2d8ff3", "#8682ed", "#bb71d9", "#e05fba", "#f65394", "#fb566f", 
            "#f4634b", "#e37529", "#c38a00", "#9c9b00", "#6da728", "#1aaf54"];
    palette = ["#2d8ff3", "#fc585e", "#1aaf54", "#e05fba", "#e37529", "#f65394"]
    styles = ["solid", "dashed", "dotted", "dashdot"]
    
    # Alternative color palette
    #palette = plt.cm.Pastel1.colors
    
    configs["palette"] = palette
    configs["styles"] = styles
            
    return configs


def read_data(path, n_max=100):
    try:
        # Optimizations:
        # - [TODO] Only read the header and the last n_max lines
        #          https://stackoverflow.com/questions/136168/
        #          https://stackoverflow.com/questions/17108250/
        # - [TODO] Use the usecols argument (if x_col and y_cols are provided)
        data = pd.read_csv(path)
        data = data.rename(columns=lambda x: x.strip())
    except pd.errors.EmptyDataError:
        return None
    if len(data) == 0:
        return None
    data = data.tail(n_max)
    return data


def read_data_until(path, timeout=60, n_max=100):
    start = time.time()
    while True:
        data = read_data(path, n_max=n_max)
        if data is not None:
            return data
        time.sleep(1.0)
        current = time.time()
        if current - start > timeout:
            return None
        
        
def check_col(data, col, warn=True):
    if col in data.columns:
        return col
    else:
        try:
            return data.columns[int(col)]
        except KeyError:
            if warn:
                print("Warning: Cannot find column %s" % col)
            return None
    return None
        
        
def organize_cols(data, x_cols, y_cols, warn=True):
    if x_cols is not None:
        x_cols = [check_col(data, col, warn) for col in x_cols]
        x_cols = [col for col in x_cols if col is not None]
        x_cols = x_cols if len(x_cols) > 0 else None
    
    if y_cols is not None:
        y_cols = [check_col(data, col, warn) for col in y_cols]
        y_cols = [col for col in y_cols if col is not None]
        y_cols = y_cols if len(y_cols) > 0 else None
    
    if x_cols is not None and y_cols is not None:
        if (len(x_cols) != len(y_cols) and len(x_cols)>1) and warn:
            print("Warning: Number of x-cols must match the number of y-cols.")
            print("Warning: Ignoring x-cols.")
            x_cols = None
    
    if x_cols is None:
        x_cols = ["_index"]
    if y_cols is None:
        y_cols = data.columns
        
    assert(len(x_cols) <= len(y_cols))
    col_pairs = list(zip(cycle(x_cols), y_cols))
    data = data.reset_index(names="_index")
    
    return data, col_pairs


def get_label(x_col, y_col):
    return y_col if (x_col=="_index") else "%s vs. %s" % (x_col, y_col)


def plot_data(ax, data, col_pairs, configs):
    styles = configs["styles"]
    palette = configs["palette"]
    colors_styles = cycle(product(styles, palette))
    
    handles = dict()
    for i, (x_col, y_col) in enumerate(col_pairs):
        ls, c = next(colors_styles)
        label = get_label(x_col, y_col)
        handle = ax.plot(data[x_col].values,
                         data[y_col].values, 
                         color=c,
                         linestyle=ls, 
                         label=label)
        # Draw the last point as a circle
        handle_p = ax.plot(data[x_col].values[-1],
                           data[y_col].values[-1], 
                           color=c, 
                           marker="o", 
                           markersize=3)
        handles[label] = handle
        handles[label+"_point"] = handle_p
    # Place legend outside the plot
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.set_title("Log Visualizer", fontweight="bold")
    x_cols, y_cols = list(zip(*col_pairs))
    x_cols = [col if col!="_index" else "Sample" for col in x_cols]
    x_cols = list(dict.fromkeys(x_cols))
    ax.set_xlabel("\n".join(x_cols), fontweight="bold")
    ax.set_ylabel("Value", fontweight="bold")
    ax.grid(axis="y", alpha=0.5)
    return handles


def plot_update(ax, handles, data, col_pairs, configs):
    if data is None:
        return
    max_samples = configs["max_samples"]
    rescale_speed = configs["rescale_speed"]
    lim_margin = configs["lim_margin"]
    x_min = np.inf
    x_max = -np.inf
    y_min = np.inf
    y_max = -np.inf
    for i, (x_col, y_col) in enumerate(col_pairs):
        label = get_label(x_col, y_col)
        x = data[x_col]
        y = data[y_col]
        if (x.dtype == "object" or y.dtype == "object"):
            # Likely an i/o error
            continue
        handles[label][0].set_ydata(y)
        handles[label][0].set_xdata(x)
        handles[label+"_point"][0].set_ydata(y[-1:])
        handles[label+"_point"][0].set_xdata(x[-1:])
        x_min = min(x_min, x.min())
        x_max = max(x_max, x.max())
        y_min = min(y_min, y.min())
        y_max = max(y_max, y.max())
    # Make this robust...
    x_min_cur, x_max_cur = ax.get_xlim()
    y_min_cur, y_max_cur = ax.get_ylim()
    dx = x_max - x_min
    dy = y_max - y_min
    # Only change the y-axis limits if they have changed 
    if np.isfinite(y_min) and np.isfinite(y_max):
        y_min_target = y_min - dy*lim_margin
        y_max_target = y_max + dy*lim_margin
        low_rel = (y_min_target - y_min_cur)/dx
        high_rel = (y_max_cur - y_max_target)/dx
        if (low_rel > 0.2 or low_rel < 0) or (high_rel > 0.2 or high_rel < 0):
            ax.set_ylim((y_min_cur + (y_min_target - y_min_cur)*0.9, 
                         y_max_cur + (y_max_target - y_max_cur)*0.9))
    # Only change the x-axis limits if they have changed 
    if np.isfinite(x_min) and np.isfinite(x_max):
        x_min_target = x_min - dx*lim_margin
        x_max_target = x_max + dx*lim_margin
        low_rel = (x_min_target - x_min_cur)/dx
        high_rel = (x_max_cur - x_max_target)/dx
        
        if (low_rel > 0.2 or low_rel < 0) or (high_rel > 0.2 or high_rel < 0):
            #ax.set_xlim(x_min_target, x_max_target)
            ax.set_xlim((x_min_cur + (x_min_target - x_min_cur)*0.9, 
                         x_max_cur + (x_max_target - x_max_cur)*0.9))
    plt.draw()


def run(configs):
    log_file = Path(configs["path_to_logs"])
    
    x_cols = configs["x_cols"]
    y_cols = configs["y_cols"]
    
    print("Log file: %s" % log_file)
    print("Waiting for log file...")

    start = time.time()
    while log_file.is_file() == False:
        time.sleep(0.1) # wait for the file
        current = time.time()
        if current - start > configs.get("timeout", 60):
            print("Timeout reached, no log file found: %s" % log_file)
            sys.exit()

    plt.ion()
    fig, ax = plt.subplots()
    data = read_data_until(log_file, 
                           timeout=configs["timeout"],
                           n_max=configs["max_samples"])
    data, col_pairs = organize_cols(data, x_cols, y_cols, warn=True)
    handles = plot_data(ax=ax, data=data, 
                        col_pairs=col_pairs, 
                        configs=configs)
    fig.tight_layout()

    while True:
        data = read_data(log_file, 
                         n_max=configs["max_samples"])
        data, col_pairs = organize_cols(data, x_cols, y_cols, warn=False)
        plot_update(ax=ax, 
                    handles=handles, 
                    data=data, 
                    col_pairs=col_pairs,
                    configs=configs)
        plt.pause(configs["sleep_time"])
        # Check if fig is still alive...
        if not plt.fignum_exists(fig.number):
            break

def run_args(args):
    configs = load_configs(args)
    run(configs)
    

if __name__ == "__main__":
    
    # Add command line arguments here
    parser = argparse.ArgumentParser(description="Plot data from a log file")
    parser.add_argument("-f", "--file", type=str, 
                        help="Path to the log file")
    parser.add_argument("-s", "--sleep", type=float, default=None,
                        help="Sleep time between updates (default: 0.05s)")
    parser.add_argument("-n", "--max-samples", type=int, default=None,
                        help="Maximum number of samples to plot (default: 100)")
    parser.add_argument("--timeout", type=int, default=None,
                        help="Timeout for log file detection (default: 10s)")
    parser.add_argument("-y", "--y-cols", "--y-col", type=str, nargs="+", default=None,
                        help=("Names or indices of the columns with y-values. "
                              "If not provided, all columns will be plotted."))
    parser.add_argument("-x", "--x-cols", "--x-col", type=str, nargs="+", default=None,
                        help=("Names or indices of the columns with x-values. "
                              "If not provided, the sample index will be used. "
                              "If multiple columns are provided, it must match "
                              "the number of y-columns."))
    args = parser.parse_args()
    run_args(args)
    
    
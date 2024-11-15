import math
import utime
import random

def f_heart(t, noise=0):
    x = 16*(math.sin(t))**3
    y = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
    if noise != 0:
        x += random.uniform(-noise, noise)
        y += random.uniform(-noise, noise)
    return x, y

def f_duerer(t, noise=0):
    x = 16*(math.sin(t))**3
    y = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
    if noise != 0:
        x += random.uniform(-noise, noise)
        y += random.uniform(-noise, noise)
    return x, y

# Print header
print("x(t), y(t), x_s(t), y_s(t)")

t_start = utime.ticks_us()
t_last = None
alpha = 0.1
x_s = y_s = None
noise = 1.5

while True:
    try:
        t = utime.ticks_us()
        dt = utime.ticks_diff(t, t_start) / 1e6
        x, y = f_duerer(dt, noise=noise)
        x_s = x if x_s is None else alpha * x + (1 - alpha) * x_s
        y_s = y if y_s is None else alpha * y + (1 - alpha) * y_s
        print("%3f,%.3f,%.3f,%.3f" % (x, y, x_s, y_s))
        
        utime.sleep(0.02)
    except RuntimeError:
        print("Retrying!")
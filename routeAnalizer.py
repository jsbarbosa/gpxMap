# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 08:07:20 2016

@author: Juan
"""

import numpy as np
import matplotlib.pyplot as plt
import gpxpy
import gpxpy.gpx
import time
import images2gif
from PIL import Image
import io
from matplotlib import animation
from matplotlib import gridspec
from scipy.signal import *

def dataWrapper(path):
    """ Gets data from gpx file .
    Returns:
        An array with the latitude, longitude, elevation, speed, and time interval in seconds.
    """
    gpx_file = open(path, 'r')
    gpx = gpxpy.parse(gpx_file)
    pointNumber = 0
    for track in gpx.tracks:
        for segment in track.segments:
            pointNumber += len(segment.points)
    data = np.zeros((pointNumber, 6))
    i = 0
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if i == 0:
                    distance = 0
                    time = 0
                else:
                    distance += gpxpy.geo.haversine_distance(point.latitude, point.longitude, 
                                                             last.latitude, last.longitude)/1000
                    time = (point.time-last.time).total_seconds()
                temp = [point.latitude, point.longitude, point.elevation, point.speed, distance, time]
                data[i] = np.array(temp) 
                last = point
                i += 1
    return data

def ceroSpeed(data):
    """ Gets the output data from dataWrapper and deletes zero speed points.
    Returns:
        An array with the latitude, longitude, elevation, speed, distance and time interval in seconds.
    """
    temp = data[:, SPEED_US]
    zeroPoints = np.count_nonzero(temp == 0)
    new_data = np.zeros((len(data)-zeroPoints, len(data[0])))
    i = 0
    for point in data:
        if point[SPEED_US] != 0:
            new_data[i] = point
            i += 1
    return new_data

def degreeConv(old):
    """ 
    Returns:
        A decimal degree from a 3D list. [0] degree, [1] minute, [2] second
    """
    return old[0] + old[1]/60 + old[2]/3600

def elapsedTime(timeArray):
    """
    Returns:
        An accumulative time count
    """
    for i in range(len(timeArray)):
        if i != 0:
            timeArray[i] += timeArray[i-1]
    return timeArray

def timeStyle(time_interval):
    """
    Returns:
        An elapsed time with the H:M:S style
    """
    return time.strftime('%H:%M', time.gmtime(time_interval))

# Loads GPS and Google Earth data
dataUS = dataWrapper("GPS-data/Loctome-Sopo.gpx")
data = np.genfromtxt("GPS-data/GoogleEarth-Sopo.txt", delimiter=",")

# Sets the column information
LATITUDE_US = 0
LONGITUDE_US = 1
ALTITUDE_US = 2
SPEED_US = 3
DISTANCE_US = 4
TIME_US = 5

TYPE_GE = 0
LATITUDE_GE = 1
LONGITUDE_GE = 2
ALTITUDE_GE = 3
COURSE_GE = 4
SLOPE_GE = 5
DISTANCE_GE = 6
DISTANCE_INTER_GE = 7
COLOR_GE = 8
WIDTH_GE = 9
OPACITY_GE = 10
NAME_GE = 11
DESC_GE = 12

# Takes off the first line from the Google Earth data
data = data[1:]

# Takes off zero speed points
dataUS = ceroSpeed(dataUS)
i = 0
while i < 6:
    dataUS[:, SPEED_US] = savgol_filter(dataUS[:, SPEED_US], 51, 9-i)#medfilt(dataUS[:, SPEED_US], 31) #wiener(dataUS[:, SPEED_US])#, noise=100.0)
    i += 1

distance = dataUS[:, DISTANCE_US]
altitude = dataUS[:, ALTITUDE_US]
time_accumulative = elapsedTime(dataUS[:, TIME_US])
# Location data
locations_lat = [[4,42,53], [4,40,20], [4,45,11], [4,54,29]]
locations_long = [[74,4,33], [74,0,38], [73,56,20], [73,57,30]]
locations_name = ["Bogota", "Patios", "La Calera", "Sopo"]

# Change location data to decimal degrees
i = 0
for (lat, long) in zip(locations_lat, locations_long):
    locations_lat[i] = degreeConv(lat)
    locations_long[i] = -degreeConv(long)       # Negative for western longitude
    i += 1

# Prints important information
max_altitude = max(altitude)
min_altitude = min(altitude)
max_distance = distance[-1]
max_speed = max(dataUS[:, SPEED_US])
total_time = timeStyle(time_accumulative[-1])
print("Max altitude %.3f m"%max_altitude)
print("Min altitude %.3f m"%min_altitude)
print("Total distance %.3f km"%max_distance)
print("Max speed %.3f km/h"%max_speed)
print("Duration", total_time)

# Plots the data
columns = 3
rows = 2
def dataPlot(path = None):
    fig = plt.figure(figsize=(4*columns, 2*rows))
    gs = gridspec.GridSpec(rows, columns)
    ax1 = fig.add_subplot(gs[:1,0])
    ax1.plot(distance, altitude)
    ax1.plot(data[:, DISTANCE_GE]+2.5, data[:, ALTITUDE_GE])
    ax1.set_ylabel("Altitude (m)")
    ax1.grid()
    
    ax2 = fig.add_subplot(gs[1:,0])
    y = dataUS[:, SPEED_US]
    aveg_speed = sum(y)/len(y)
    ax2.plot(distance, y)
    ax2.text(60, 45, "%.2f km/h"%aveg_speed)
    ax2.set_ylabel("Speed (km/h)")
    ax2.grid()
    
    ax3 = fig.add_subplot(gs[:, 1:])
    ax3.plot(dataUS[:, LATITUDE_US], dataUS[:, LONGITUDE_US])
    ax3.plot(data[:, LATITUDE_GE], data[:, LONGITUDE_GE])
    for (lat, long, name) in zip(locations_lat, locations_long, locations_name):
        ax3.text(lat, long, name)
    ax3.set_xlabel("Latitude (decimal degrees)")
    ax3.set_ylabel("Longitude (decimal degrees)")
    ax3.set_ylim(ax3.get_ylim()[::-1])
    ax3.grid()
    
    plt.tight_layout()      # Improves layout
    if path != None:
        try:
            plt.savefig(path)
            plt.close()
        except:
            print("Invalid path or extention")
    else:
        plt.show()
          
def animationMethod(path = None):

    """
    Animation
    """
    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure(figsize=(4*columns, 2*rows))
    lines = []
    points = []
    texts = []    
    
    gs = gridspec.GridSpec(rows, columns)
    ax1 = fig.add_subplot(gs[:1,0])
    ax1.set_xlim(min(distance), max(distance))
    ax1.set_ylim(min(altitude), max(altitude))
    ax1.grid()
    ax1.set_ylabel("Altitude (m)")
    ax1.text(40, 2950, "Altitude (m)")
    
    line, = ax1.plot([], [])
    point, = ax1.plot([], [], "o", color = "red")
    text = ax1.text(60, 2900, "")
    lines.append(line)
    points.append(point)
    texts.append(text)
    
    ax2 = fig.add_subplot(gs[1:,0])
    ax2.set_xlim(min(distance), max(distance))
    ax2.set_ylim(min(dataUS[:, SPEED_US]), max(dataUS[:, SPEED_US]))
    ax2.grid()
    ax2.set_ylabel("Speed (km/h)")
    ax2.set_xlabel("Distance (km)")
    ax2.text(40, 45, "Speed (km/h)")
    
    line, = ax2.plot([], [])
    point, = ax2.plot([], [], "o", color = "red")
    text = ax2.text(60, 40, "")
    lines.append(line)
    points.append(point)    
    texts.append(text)
    
    ax3 = fig.add_subplot(gs[:,1:])
    ax3.set_ylim(max(dataUS[:, LONGITUDE_US]), min(dataUS[:, LONGITUDE_US]))
    ax3.set_xlim(min(dataUS[:, LATITUDE_US]), max(dataUS[:, LATITUDE_US]))
    ax3.grid()
    ax3.set_xlabel("Latitude (decimal degrees)")
    ax3.set_ylabel("Longitude (decimal degrees)")
    ax3.plot(dataUS[:, LATITUDE_US], dataUS[:, LONGITUDE_US], color="black", alpha = 0.3)
    for (lat, long, name) in zip(locations_lat, locations_long, locations_name):
        ax3.text(lat, long, name)
    ax3.text(4.85, -74.07, "Elapsed time")
    line, = ax3.plot([], [])
    point, = ax3.plot([], [], "o", color="red")
    text = ax3.text(4.90,-74.07, "")
    lines.append(line)
    points.append(point)
    texts.append(text)
    plt.tight_layout()
    
    lines_data = [[distance, altitude], [distance, dataUS[:, SPEED_US]], [dataUS[:, LATITUDE_US], dataUS[:, LONGITUDE_US]]]
    timeStyled = [timeStyle(temp) for temp in time_accumulative]
    speedText = ["%.1f"%temp for temp in dataUS[:, SPEED_US]] 
    texts_data = [altitude, speedText, timeStyled]
    figList = []
    repeat = True
    if path != None:
        repeat = False
    
    # initialization function: plot the background of each frame
    def init():
        for line in lines:
            line.set_data([], [])
        for point in points:
            point.set_data([], [])
        for text in texts:
            text.set_text("")
        return tuple(lines) + tuple(points) + tuple(texts)
    
    # animation function.  This is called sequentially
    def animate(i):
        for (line, line_data) in zip(lines, lines_data):
            line.set_data(line_data[0][:i], line_data[1][:i])
        for (point, point_data) in zip(points, lines_data):
            point.set_data(point_data[0][i], point_data[1][i])
        for (text, text_data) in zip(texts, texts_data):
            text.set_text(text_data[i])
        if i%100 == 0 and not repeat:
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            im = Image.open(buf)
            figList.append(im)
        return tuple(lines) + tuple(points) + tuple(texts)
    
    
    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=len(distance), interval=0, repeat = repeat, blit=True)
    
    plt.show()
    if not repeat:
        images2gif.writeGif(path, figList)#, duration=FRAME_DELAY, loops=10, dither=0)

#dataPlot()
print("Begin")
animationMethod("Animated.gif")
print("Done")

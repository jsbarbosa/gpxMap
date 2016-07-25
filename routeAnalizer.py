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
from matplotlib import animation
from matplotlib import gridspec

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
dataUS = dataWrapper("JuanBarbosa.gpx")
data = np.genfromtxt("Route.txt", delimiter=",")

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
        

j = 0    
def animationMethod(path = None):

    """
    Animation
    """
    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure(figsize=(4*columns, 2*rows))
    gs = gridspec.GridSpec(rows, columns)
    ax1 = fig.add_subplot(gs[:1,0])
    ax1.set_xlim(min(distance), max(distance))
    ax1.set_ylim(min(altitude), max(altitude))
    ax1.grid()
    ax1.set_ylabel("Altitude (m)")
    line_US, = ax1.plot([], [])
    point_US, = ax1.plot([], [], "o", color = "red", ms=1)
    
    ax2 = fig.add_subplot(gs[1:,0])
    ax2.set_xlim(min(distance), max(distance))
    ax2.set_ylim(min(dataUS[:, SPEED_US]), max(dataUS[:, SPEED_US]))
    ax2.grid()
    ax2.set_ylabel("Speed (km/h)")
    ax2.set_xlabel("Distance (km)")
    speed_US, = ax2.plot([], [])
    point_speed, = ax2.plot([], [], "o", color = "red")
    
    ax3 = fig.add_subplot(gs[:,1:])
    ax3.set_ylim(max(dataUS[:, LONGITUDE_US]), min(dataUS[:, LONGITUDE_US]))
    ax3.set_xlim(min(dataUS[:, LATITUDE_US]), max(dataUS[:, LATITUDE_US]))
    ax3.grid()
    ax3.set_xlabel("Latitude (decimal degrees)")
    ax3.set_ylabel("Longitude (decimal degrees)")
    ax3.plot(dataUS[:, LATITUDE_US], dataUS[:, LONGITUDE_US], color="black", alpha = 0.3)
    for (lat, long, name) in zip(locations_lat, locations_long, locations_name):
        ax3.text(lat, long, name)
    position_US, = ax3.plot([], [])
    us, = ax3.plot([], [], "o", color="red")
    time_display = ax3.text(4.90,-74.07, "")
    plt.tight_layout()
    j = 0
    
    # initialization function: plot the background of each frame
    def init():
        line_US.set_data([], [])
        point_US.set_data([], [])
        speed_US.set_data([], [])
        point_speed.set_data([], [])
        position_US.set_data([], [])
        us.set_data(dataUS[0, LATITUDE_US], dataUS[0: LONGITUDE_US])
        time_display.set_text("")
        return line_US, point_US, speed_US, point_speed, position_US, us, time_display
    
    # animation function.  This is called sequentially
    def animate(i):
        global j      
#        global max_altitude, min_altitude, max_distance, max_speed
        line_US.set_data(distance[:i], altitude[:i])
        coeff = (altitude[i]-min_altitude)/(max_altitude-min_altitude)
        if coeff >= 1/3:
            point_US.set_markersize(6*coeff)
        point_US.set_data(distance[i], altitude[i])
        y = dataUS[:, SPEED_US]
        speed_US.set_data(distance[:i], y[:i])
        point_speed.set_data(distance[i], y[i])
        coeff = y[i]/max_speed
        if coeff >= 1/3:
            point_speed.set_markersize(6*coeff)
        x = dataUS[:, LATITUDE_US]
        y = dataUS[:, LONGITUDE_US]
        position_US.set_data(x[:i], y[:i])
        us.set_data(x[i], y[i])
        us.set_markersize(12*(distance[i]/max_distance))
        time_display.set_text(timeStyle(time_accumulative[i]))
        if i%100 == 0 and path != None:
            fig.savefig(path+str(j)+".png")
            j += 1
        return line_US, point_US, speed_US, point_speed, position_US, us, time_display
    
    # call the animator.  blit=True means only re-draw the parts that have changed.
    interval = 0
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=len(distance), interval=interval, blit=True)
    
#    if path != None:
#        anim.save(path, fps=120)#, extra_args=['-vcodec', 'libx264'])
    
    plt.show()

dataPlot("Results.png")
print("Begin")
animationMethod("Frames")
print("Done")
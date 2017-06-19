# -*- coding: utf-8 -*-
"""
@author: Juan
"""

import io
import time
import gpxpy
import gpxpy.gpx
import numpy as np
from PIL import Image
import matplotlib as mpl
from scipy.signal import *
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib import animation

mpl.rcParams['grid.color'] = 'k'
mpl.rcParams['grid.linestyle'] = ':'
mpl.rcParams['grid.linewidth'] = 0.5

class Location(object):
    def __init__(self, name, lat, long_, convert_to_degree = True):
        self.name = name
        self.latitude = lat
        self.longitude = long_
        if convert_to_degree:
            self.latitude = self.degreeConv(lat)
            self.longitude = self.degreeConv(long_)

    def degreeConv(self, old):
        """
        Returns:
            A decimal degree from a 3D list. [0] degree, [1] minute, [2] second
        """
        return old[0] + old[1]/60 + old[2]/3600

class Route(object):
    # Sets the column information
    LATITUDE = 0
    LONGITUDE = 1
    ALTITUDE = 2
    SPEED = 3
    DISTANCE = 4
    TIME = 5

    def __init__(self, data):
        self.data = data

        self.latitude = self.data[:, self.LATITUDE]
        self.longitude = self.data[:, self.LONGITUDE]
        self.altitude = self.data[:, self.ALTITUDE]
        self.speed = self.data[:, self.SPEED]
        self.distance = self.data[:, self.DISTANCE]
        self.time = self.data[:, self.TIME]
        self.npoints = len(self.latitude)
        self.elapsed_time = self.elapsedTime()
        self.time_styled = [self.timeStyle(time) for time in self.elapsed_time]

        self.max_altitude = max(self.altitude)
        self.min_altitude = min(self.altitude)
        self.max_distance = self.distance[-1]
        self.max_speed = max(self.speed)
        self.min_speed = min(self.speed)
        self.mean_speed = sum(self.speed)/self.npoints
        self.total_time = self.time_styled[-1]

    def printImportant(self):
        print("Max altitude %.3f m"%self.max_altitude)
        print("Min altitude %.3f m"%self.min_altitude)
        print("Total distance %.3f km"%self.max_distance)
        print("Max speed %.3f km/h"%self.max_speed)
        print("Mean speed %.3f km/h"%self.mean_speed)
        print("Duration", self.total_time)

    def ceroSpeed(self):
        """ Gets the output data from dataWrapper and deletes zero speed points.
        Returns:
            An array with the latitude, longitude, elevation, speed, distance and time interval in seconds.
        """
        temp = self.data[:, self.SPEED]
        zeroPoints = np.count_nonzero(temp == 0)
        new_data = np.zeros((self.data.shape[0]-zeroPoints, self.data.shape[1]))
        i = 0
        for point in self.data:
            if point[self.SPEED] != 0:
                new_data[i] = point
                i += 1
        return Route(new_data)

    def elapsedTime(self):
        """
        Returns:
            An accumulative time count
        """
        time = np.zeros_like(self.time)
        for i in range(self.npoints):
            if i != 0:
                time[i] = time[i-1] + self.time[i]
        return time

    def timeStyle(self, time_interval):
        """
        Returns:
            An elapsed time with the H:M:S style
        """
        return time.strftime('%H:%M', time.gmtime(time_interval))

def dataWrapper(path):
    """ Gets data from gpx file .
    Returns:
        An array with the latitude, longitude, elevation, speed, and time interval in seconds.
    """
    with open(path, 'r') as gpx_file:
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

def dataPlot(route, locations = None, path = None):
    fig = plt.figure(figsize=(12, 4))
    gs = gridspec.GridSpec(2, 3)

    ax1 = fig.add_subplot(gs[:1,0])
    ax1.plot(route.distance, route.altitude)
    ax1.set_ylabel("Altitude (m)")
    ax1.grid()

    ax2 = fig.add_subplot(gs[1:,0])
    ax2.plot(route.distance, route.speed)
    ax2.text(60, 45, "%.2f km/h"%route.mean_speed)
    ax2.set_ylabel("Speed (km/h)")
    ax2.grid()

    ax3 = fig.add_subplot(gs[:, 1:])
    ax3.plot(route.latitude, route.longitude)

    if locations != None:
        for loc in locations:
            ax3.text(loc.latitude, loc.longitude, loc.name)

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

def animationMethod(route, locations = None, jump = 1, path = None):
    """
    Animation
    """
    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure(figsize=(12, 4))
    gs = gridspec.GridSpec(2, 3)
    lines = []
    points = []
    texts = []

    altitude_xloc = 2*route.max_distance/5
    altitude_yrange = route.max_altitude - route.min_altitude
    altitude_yloc = route.max_altitude - altitude_yrange/5
    ax1 = fig.add_subplot(gs[:1,0])

    line, = ax1.plot([], [])
    point, = ax1.plot([], [], "o", color = "red")
    text = ax1.text(altitude_xloc*1.1, altitude_yloc-altitude_yrange*0.1, "")
    ax1.set_xlim(0, route.max_distance)
    ax1.set_ylim(route.min_altitude, route.max_altitude)
    ax1.text(altitude_xloc, altitude_yloc, "Altitude (m)")
    ax1.set_ylabel("Altitude (m)")
    ax1.grid()
    lines.append(line)
    points.append(point)
    texts.append(text)

    speed_yloc = (1 - 1/5)*route.max_speed
    ax2 = fig.add_subplot(gs[1:,0])
    line, = ax2.plot([], [])
    point, = ax2.plot([], [], "o", color = "red")
    text = ax2.text(altitude_xloc*1.1, speed_yloc*0.9, "")
    ax2.text(altitude_xloc, speed_yloc,"Speed (km/h)")
    ax2.set_xlim(0, route.max_distance)
    ax2.set_ylim(route.min_speed, route.max_speed)
    ax2.set_ylabel("Speed (km/h)")
    ax2.set_xlabel("Distance (km)")

    ax2.grid()
    lines.append(line)
    points.append(point)
    texts.append(text)

    location_xrange = max(route.latitude) - min(route.latitude)
    location_xloc = max(route.latitude) - (2/6)*location_xrange
    location_yrange = max(route.longitude) - min(route.longitude)
    location_yloc = min(route.longitude) + (1/8)*location_yrange
    ax3 = fig.add_subplot(gs[:,1:])
    line, = ax3.plot([], [])
    point, = ax3.plot([], [], "o", color="red")
    text = ax3.text(location_xloc + location_xrange*0.1, location_yloc + 0.05*location_yrange, "")
    ax3.set_ylim(max(route.longitude), min(route.longitude))
    ax3.set_xlabel("Latitude (decimal degrees)")
    ax3.set_ylabel("Longitude (decimal degrees)")
    ax3.plot(route.latitude, route.longitude, color="black", alpha = 0.3)
    ax3.text(location_xloc, location_yloc, "Elapsed time")

    if locations != None:
        for loc in locations:
            ax3.text(loc.latitude, loc.longitude, loc.name)

    ax3.grid()
    lines.append(line)
    points.append(point)
    texts.append(text)
    plt.tight_layout()

    lines_data = [[route.distance, route.altitude],
                [route.distance, route.speed],
                [route.latitude, route.longitude]]

    speedText = ["%.1f"%speed for speed in route.speed]
    texts_data = [route.altitude, speedText, route.time_styled]

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
        i *= jump
        for (line, line_data) in zip(lines, lines_data):
            line.set_data(line_data[0][:i], line_data[1][:i])
        for (point, point_data) in zip(points, lines_data):
            point.set_data(point_data[0][i], point_data[1][i])
        for (text, text_data) in zip(texts, texts_data):
            text.set_text(text_data[i])

        return tuple(lines) + tuple(points) + tuple(texts)


    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=route.npoints//jump, interval=0, blit=True)

    if path != None:
        anim.save(path, writer="imagemagick", fps=24)
    else:
        plt.show()

Bogota = Location("Bogota", [4,42,53], [-74, -4, -33])
Patios = Location("Patios", [4, 40, 20], [-74, -0, -38])
LaCalera = Location("La Calera", [4, 45, 11], [-73, -56, -20])
Sopo = Location("Sopo", [4, 54, 29], [-73, -57, -30])

if __name__ == "__main__":
    locations = [Bogota, Patios, LaCalera, Sopo]

    route = Route(dataWrapper("GPS-data/Loctome-Teusaca_2017-06-18.gpx"))
    route = Route(dataWrapper("GPS-data/Loctome-Sopo.gpx"))
    non_stop = route.ceroSpeed()
    non_stop.printImportant()

    # dataPlot(non_stop, locations)
    animationMethod(non_stop, locations, jump=non_stop.npoints//120, path="Sopo.gif")

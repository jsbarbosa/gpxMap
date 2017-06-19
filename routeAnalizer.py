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

from urllib.request import urlopen

mpl.rcParams['grid.color'] = 'k'
mpl.rcParams['grid.linestyle'] = ':'
mpl.rcParams['grid.linewidth'] = 0.5

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

        # geo
        self.min_latitude = min(self.latitude)
        self.max_latitude = max(self.latitude)
        self.min_longitude = min(self.longitude)
        self.max_longitude = max(self.longitude)
        self.center = 0.5*(self.min_latitude + self.max_latitude),\
                    0.5*(self.min_longitude + self.max_longitude)

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

class Map(object):
    """TAKEN"""
    EARTH_RADIUS = 6378137
    EQUATOR_CIRCUMFERENCE = 2 * np.pi * EARTH_RADIUS
    INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
    ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0
    SIZE = (600, 600)

    def __init__(self, route, maptype="roadmap"):
        self.route = route

        self.maptype = maptype
        self.center = self.route.center
        self.getZoom()

        self.upper_left_latlong = None
        self.lower_right_latlong = None
        self.mpl_extent = None

        temp = self.getLatLong()
        self.upper_left_latlong = temp[0]
        self.lower_right_latlong = temp[1]
        longs = self.lower_right_latlong[0], self.upper_left_latlong[0]
        lats = self.upper_left_latlong[1], self.lower_right_latlong[1]
        self.mpl_extent = [min(longs),
                        max(longs),
                        min(lats),
                        max(lats)]

        self.static_map = self.getStaticMap()

        self.mpl_origin = 'upper'
        if self.upper_left_latlong[1] < 0:
            self.mpl_origin = 'lower'

    def LatLonToMeters(self, lat, lon):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        mx = lon * self.ORIGIN_SHIFT / 180.0
        my = np.log( np.tan((90 + lat) * np.pi / 360.0 )) / (np.pi / 180.0)

        my = my * self.ORIGIN_SHIFT / 180.0
        return mx, my


    def MetersToPixels(self, mx, my, zoom):
        "Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"

        res = self.Resolution(zoom)
        px = (mx + self.ORIGIN_SHIFT) / res
        py = (my + self.ORIGIN_SHIFT) / res
        return px, py

    def Resolution(self, zoom):
        return self.INITIAL_RESOLUTION/(2**self.zoom)

    def PixelsToMeters(self, px, py, zoom):
        "Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

        res = self.Resolution(zoom)
        mx = px * res - self.ORIGIN_SHIFT
        my = py * res - self.ORIGIN_SHIFT
        return mx, my

    def MetersToLatLon(self, mx, my):
        "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

        lon = (mx / self.ORIGIN_SHIFT) * 180.0
        lat = (my / self.ORIGIN_SHIFT) * 180.0

        lat = 180 / np.pi * (2 * np.arctan(np.exp(lat * np.pi / 180.0)) - np.pi / 2.0)
        return lat, lon

    def getLatLong(self):
        meters = self.LatLonToMeters(self.center[0], self.center[1])
        pixels = self.MetersToPixels(meters[0], meters[1], self.zoom)

        cpx, cpy = pixels
        upper_left = cpx + self.SIZE[0]*0.5, cpy - self.SIZE[1]*0.5
        lower_right = cpx - self.SIZE[0]*0.5, cpy + self.SIZE[1]*0.5

        corners = [upper_left, lower_right]
        for (i, corner) in enumerate(corners):
            meters = self.PixelsToMeters(corner[0], corner[1], self.zoom)
            latlong = self.MetersToLatLon(meters[0], meters[1])
            corners[i] = latlong[::-1]

        return corners

    def getUrlStaticMap(self, center):
        url = "http://maps.google.com/maps/api/staticmap?"
        if center != None:
            url += "center=%s&"%center
        url += "size=%dx%d&"%(self.SIZE[0], self.SIZE[1])
        url += "zoom=%d&"%self.zoom
        url += "maptype=%s&"%self.maptype
        url += "sensor=false"
        return url

    def getStaticMap(self):
        center = "%f,%f"%(self.center[0], self.center[1])
        url = self.getUrlStaticMap(center)
        f = urlopen(url)
        a = plt.imread(f)
        return a


    def getZoom(self):
        lat_range = self.route.max_latitude - self.route.min_latitude
        long_range = self.route.max_longitude - self.route.min_longitude
        for i in range(14, 0, -1):
            self.zoom = i
            upper_left, lower_right = self.getLatLong()
            longs = lower_right[0], upper_left[0]
            lats = upper_left[1], lower_right[1]
            if long_range <= max(longs) - min(longs):
                if lat_range <= max(lats) - min(lats):
                    break


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

def dataPlot(route, map_ = None, path = None):
    fig = plt.figure(figsize=(10, 4))
    gs = gridspec.GridSpec(2, 2)

    ax1 = fig.add_subplot(gs[:1,0])
    ax1.plot(route.distance, route.altitude)
    ax1.set_ylabel("Altitude (m)")
    ax1.grid()

    ax2 = fig.add_subplot(gs[1:,0])
    ax2.plot(route.distance, route.speed)
    ax2.text(60, 45, "%.2f km/h"%route.mean_speed)
    ax2.set_ylabel("Speed (km/h)")
    ax2.grid()

    ax3 = fig.add_subplot(gs[:, 1])
    if map_ != None:
        ax3.imshow(map_.static_map, extent=map_.mpl_extent, origin=map_.mpl_origin)
    ax3.plot(route.longitude, route.latitude)

    ax3.set_xlabel("Longitude (decimal degrees)")
    ax3.set_ylabel("Latitude (decimal degrees)")
    ax3.grid()

    # plt.tight_layout()      # Improves layout
    if path != None:
        plt.savefig(path)
        plt.close()
    else:
        plt.show()

def animationMethod(route, map_ = None, jump = 1, path = None, dpi = 100):
    """
    Animation
    """
    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure(figsize=(10, 4))
    gs = gridspec.GridSpec(2, 2)
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

    ax3 = fig.add_subplot(gs[:,1:])

    if map_ != None:
        ax3.imshow(map_.static_map, extent=map_.mpl_extent, origin=map_.mpl_origin)

    line, = ax3.plot([], [])
    point, = ax3.plot([], [], "o", color="red")

    xlim = ax3.get_xlim()
    ylim = ax3.get_ylim()
    box = dict(boxstyle='round', facecolor='white', alpha=0.7)
    text = ax3.text(0.5*(xlim[0]+xlim[1]), ylim[1] - 0.1*(ylim[1]-ylim[0]), "", bbox=box)
    ax3.set_xlabel("Longitude (decimal degrees)")
    ax3.set_ylabel("Latitude (decimal degrees)")
    alpha = 0.3
    if map_.maptype == "satellite":
        alpha = 0.8
    ax3.plot(route.longitude, route.latitude, lw=0.5, color="black", alpha = alpha)

    ax3.grid()
    lines.append(line)
    points.append(point)
    texts.append(text)
    plt.subplots_adjust(top=1.1)
    plt.tight_layout()

    lines_data = [[route.distance, route.altitude],
                [route.distance, route.speed],
                [route.longitude, route.latitude]]

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
        anim.save(path, writer="imagemagick", fps=24, dpi=dpi)
    else:
        plt.show()

if __name__ == "__main__":
    route = Route(dataWrapper("GPS-data/Loctome-Sopo.gpx"))
    myMap = Map(route, maptype="satellite")

    non_stop = route.ceroSpeed()
    non_stop.printImportant()
    # dataPlot(non_stop, myMap)

    animationMethod(non_stop, myMap, jump=non_stop.npoints//120)#, path="Sopo.gif")

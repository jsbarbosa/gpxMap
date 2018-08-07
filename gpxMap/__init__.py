# -*- coding: utf-8 -*-
"""
@author: Juan
"""

import io
import time
import gpxpy
import gpxpy.gpx
from PIL import Image
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib import animation

from urllib.request import urlopen

import warnings

import math

# import numpy as np
# from scipy.signal import *

mpl.rcParams['grid.color'] = 'k'
mpl.rcParams['grid.linestyle'] = ':'
mpl.rcParams['grid.linewidth'] = 0.25

__version__ = "0.0.1"

class Route(object):
    # Sets the column information
    LATITUDE = 0
    LONGITUDE = 1
    ALTITUDE = 2
    SPEED = 3
    DISTANCE = 4
    TIME = 5

    def __init__(self, data):
        if type(data) is dict:
            self.data = data
        else:
            self.data = dataWrapper(data)

        self.npoints = len(self.data['latitude'])
        self.elapsed_time = self.elapsedTime()
        self.time_styled = [self.timeStyle(time) for time in self.elapsed_time]

        self.max_distance = self.data['distance'][-1]

        self.setSpeed(self.data['speed'])
        self.setElevation(self.data['elevation'])

        self.total_time = self.time_styled[-1]

        # geo
        self.min_latitude = min(self.data['latitude'])
        self.max_latitude = max(self.data['latitude'])
        self.min_longitude = min(self.data['longitude'])
        self.max_longitude = max(self.data['longitude'])
        self.center = 0.5*(self.min_latitude + self.max_latitude),\
                    0.5*(self.min_longitude + self.max_longitude)

    def printImportant(self):
        print("Max altitude %.3f m"%self.max_altitude)
        print("Min altitude %.3f m"%self.min_altitude)
        print("Total distance %.3f km"%self.max_distance)
        print("Max speed %.3f km/h"%self.max_speed)
        print("Mean speed %.3f km/h"%self.mean_speed)
        print("Duration", self.total_time)

    def setSpeed(self, speed):
        speed = [round(s, 1) for s in speed]
        self.max_speed = max(speed)
        self.min_speed = min(speed)
        self.mean_speed = sum(speed) / self.npoints
        self.data['speed'] = speed

    def setElevation(self, altitude):
        altitude = [round(a, 1) for a in altitude]
        self.max_altitude = max(altitude)
        self.min_altitude = min(altitude)
        self.data['elevation'] = altitude

    def getMaxElevation(self):
        return self.max_altitude

    def getMinElevation(self):
        return self.min_altitude

    def getMaxDistance(self):
        return self.max_distance

    def getTotalTime(self):
        return self.total_time

    def getMaxSpeed(self):
        return self.max_speed

    def getMinSpeed(self):
        return self.min_speed

    def getMeanSpeed(self):
        return self.mean_speed

    def getSpeed(self):
        return self.data['speed']

    def getLatitude(self):
        return self.data['latitude']

    def getLongitude(self):
        return self.data['longitude']

    def getTime(self):
        return self.data['time']

    def getElevation(self):
        return self.data['elevation']

    def getDistance(self):
        return self.data['distance']

    def getStyledTime(self):
        return self.time_styled

    def getNumberPoints(self):
        return self.npoints

    def elapsedTime(self):
        """
        Returns:
            An accumulative time count
        """
        times = [0] * self.npoints

        for i in range(1, self.npoints):
            times[i] = times[i - 1] + self.data['time'][i]

        return times

    def getCreator(self):
        return self.data['creator']

    def timeStyle(self, time_interval):
        """
        Returns:
            An elapsed time with the H:M:S style
        """
        return time.strftime('%H:%M', time.gmtime(time_interval))

class Map(object):
    """TAKEN"""
    EARTH_RADIUS = 6378137
    EQUATOR_CIRCUMFERENCE = 2 * math.pi * EARTH_RADIUS
    INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
    ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0
    SIZE = (600, 600)
    MAP_TYPES = ["roadmap", "satellite", "terrain", "hybrid"]

    def __init__(self, route, maptype = "hybrid"):
        """
            maptypes: roadmap, satellite, terrain, hybrid
        """
        if type(route) is Route:
            self.route = route
        else:
            self.route = Route(route)

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


        self.setMapType(maptype)

        self.mpl_origin = 'upper'
        if self.upper_left_latlong[1] < 0:
            self.mpl_origin = 'lower'

    def LatLonToMeters(self, lat, lon):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        mx = lon * self.ORIGIN_SHIFT / 180.0
        my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)

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

        lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
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
        for i in range(20, 0, -1):
            self.zoom = i
            upper_left, lower_right = self.getLatLong()
            longs = lower_right[0], upper_left[0]
            lats = upper_left[1], lower_right[1]
            if long_range <= max(longs) - min(longs):
                if lat_range <= max(lats) - min(lats):
                    break

    def getStatic(self):
        return self.static_map

    def getMplExtent(self):
        return self.mpl_extent

    def getMplOrigin(self):
        return self.mpl_origin

    def setMapType(self, maptype):
        if (maptype in self.MAP_TYPES):
            self.maptype = maptype
        else:
            txt = ", ".join(self.MAP_TYPES)
            raise(Exception("'%s' is not a valid map type. Types are: %s"%(str(maptype), txt)))

        self.static_map = self.getStaticMap()

class Graphics(object):
    def __init__(self, route, map_ = None):
        if type(route) is Route:
            self.route = route
            self.map = map_

        else:
            self.route = Route(route)
            self.map = Map(route)

    def getNumberPoints(self):
        return self.route.getNumberPoints()

    def setMapType(self, maptype):
        self.map.setMapType(maptype)

    def makeFigure(self, figsize = (8, 4.5)):
        fig = plt.figure(figsize = figsize)
        return fig

    def makeAxis(self, figure, grid = True):
        gs = gridspec.GridSpec(2, 2)
        ax1 = figure.add_subplot(gs[:1,0])
        ax1.set_ylabel("Elevation (m)")

        ax2 = figure.add_subplot(gs[1:,0])
        ax2.set_ylabel("Speed (km/h)")
        ax2.set_xlabel("Distance (km)")

        ax3 = figure.add_subplot(gs[:, 1])
        if self.map != None:
            ax3.imshow(self.map.getStatic(), extent = self.map.getMplExtent(), origin = self.map.getMplOrigin())

        ax3.set_xlabel("Longitude (decimal degrees)")
        ax3.set_ylabel("Latitude (decimal degrees)")

        ax3.set_title(self.route.getCreator(), fontsize = 6)

        if grid:
            ax1.grid()
            ax2.grid()
            ax3.grid()

        plt.tight_layout()      # Improves layout

        return ax1, ax2, ax3

    def plot(self, path = None, dpi = 240, figure = None, axis = None, show = True):
        if figure == None:
            figure = self.makeFigure()
        if axis == None:
            ax1, ax2, ax3 = self.makeAxis(figure)
        else:
            ax1, ax2, ax3 = axis

        ax1.plot(self.route.getDistance(), self.route.getElevation())
        ax2.plot(self.route.getDistance(), self.route.getSpeed())
        ax2.text(60, 45, "%.2f km/h"%self.route.getMeanSpeed())

        ax3.plot(self.route.getLongitude(), self.route.getLatitude())

        if show:
            plt.show()
        if path != None:
            plt.savefig(path, dpi = dpi)
            plt.close()

        return figure

    def animate(self, path = None, dpi = 240, jump = 1, figure = None, axis = None):
        def animate(i):
            i *= jump
            for (line, line_data) in zip(lines, lines_data):
                line.set_data(line_data[0][:i], line_data[1][:i])
            for (point, point_data) in zip(points, lines_data):
                point.set_data(point_data[0][i], point_data[1][i])
            for (text, text_data) in zip(texts, texts_data):
                    text.set_text(text_data[i])
            return tuple(lines) + tuple(points) + tuple(texts)

        lines = []
        points = []
        texts = []
        if figure == None:
            figure = self.makeFigure()
        if axis == None:
            ax1, ax2, ax3 = self.makeAxis(figure)
        else:
            ax1, ax2, ax3 = axis

        altitude_xloc = 2 * self.route.getMaxDistance() / 5
        altitude_yrange = self.route.getMaxElevation() - self.route.getMinElevation()
        altitude_yloc = self.route.getMaxElevation() - altitude_yrange / 5

        line, = ax1.plot([], [])
        point, = ax1.plot([], [], "o", color = "red")
        text = ax1.text(altitude_xloc * 1.1, altitude_yloc - altitude_yrange * 0.1, "")

        ax1.set_xlim(0, self.route.getMaxDistance())
        ax1.set_ylim(self.route.getMinElevation(), self.route.getMaxElevation())
        ax1.text(altitude_xloc, altitude_yloc, "Elevation (m)")

        lines.append(line)
        points.append(point)
        texts.append(text)

        speed_yloc = (1 - 1 / 5) * self.route.getMaxSpeed()
        line, = ax2.plot([], [])
        point, = ax2.plot([], [], "o", color = "red")
        ax2.set_xlim(0, self.route.getMaxDistance())
        text = ax2.text(altitude_xloc * 1.1, speed_yloc * 0.9, "")

        if self.route.getMaxSpeed() > 0:
            ax2.text(altitude_xloc, speed_yloc, "Speed (km/h)")
            ax2.set_ylim(self.route.getMinSpeed(), self.route.getMaxSpeed())
            # texts.append(text)

        lines.append(line)
        points.append(point)
        texts.append(text)

        xlim = ax3.get_xlim()
        ylim = ax3.get_ylim()
        box = dict(boxstyle = 'round', facecolor = 'white', alpha = 0.7)
        text = ax3.text(0.5 * (xlim[0] + xlim[1]), ylim[1] - 0.1 * (ylim[1]-ylim[0]), "", bbox = box)
        alpha = 0.3
        if self.map.maptype == "satellite" or self.map.maptype == "hybrid":
            alpha = 1.0

        ax3.plot(self.route.getLongitude(), self.route.getLatitude(), lw = 1.0, color="white", alpha = alpha)
        line, = ax3.plot([], [])
        point, = ax3.plot([], [], "o", color="red")

        lines.append(line)
        points.append(point)
        texts.append(text)
        plt.subplots_adjust(top = 1.1)
        plt.tight_layout()

        lines_data = [[self.route.getDistance(), self.route.getElevation()],
                        [self.route.getDistance(), self.route.getSpeed()],
                        [self.route.getLongitude(), self.route.getLatitude()]]

        if self.route.getMaxSpeed() > 0:
            speedText = ["%.1f"%speed for speed in self.route.getSpeed()]
        else:
            speedText = ["" for speed in self.route.getSpeed()]

        texts_data = [self.route.getElevation(), speedText, self.route.getStyledTime()]

        anim = animation.FuncAnimation(figure, animate, frames = self.route.npoints // jump, interval = 0, blit = True)

        if path != None:
            if path[:-3] == ".gif":
                print("Saving gif...")
                anim.save(path, writer = "imagemagick", fps = 24, dpi = dpi)
            else:
                print("Saving file...")
                anim.save(path, fps = 24, dpi = dpi)
        else:
            plt.show()

def dataWrapper(path):
    """
    Gets data from gpx file
    Returns:
        A dictionary with the latitude, longitude, elevation, speed, and time interval in seconds.
    """
    with open(path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        pointNumber = 0
        for track in gpx.tracks:
            for segment in track.segments:
                pointNumber += len(segment.points)
        data = {'latitude' : [],
                'longitude' : [],
                'elevation' : [],
                'speed' : [],
                'distance' : [],
                'time' : []}
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
                    data['latitude'].append(point.latitude)
                    data['longitude'].append(point.longitude)
                    data['elevation'].append(point.elevation)
                    if point.speed == None:
                        warnings.warn("There is no speed data. Data will be filled with zeros.")
                        data['speed'].append(0)
                    else:
                        data['speed'].append(point.speed)
                    data['distance'].append(distance)
                    data['time'].append(time)
                    last = point
                    i += 1
    data['creator'] = gpx.creator
    return data

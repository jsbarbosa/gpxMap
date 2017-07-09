import numpy as np
import matplotlib.pyplot as plt

from urllib.request import urlopen

class Map(object):
    """TAKEN"""
    EARTH_RADIUS = 6378137
    EQUATOR_CIRCUMFERENCE = 2 * np.pi * EARTH_RADIUS
    INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
    ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0
    SIZE = (600, 580)
    CUTOFF = 20

    def __init__(self, lat, lon, zoom = 17, maptype="hybrid"):
        """
            maptypes: roadmap, satellite, terrain, hybrid
        """
        self.zoom = zoom
        self.center = lat, lon

        # self.route = route
        #
        self.maptype = maptype
        # self.center = self.route.center
        # self.getZoom()
        self.Resolution()
        #
        # self.upper_left_latlong = None
        # self.lower_right_latlong = None
        # self.mpl_extent = None
        #
        temp = self.getLatLong(self.center)
        self.upper_left_latlong = temp[0]
        self.lower_right_latlong = temp[1]

        # longs = self.lower_right_latlong[0], self.upper_left_latlong[0]
        # lats = self.upper_left_latlong[1], self.lower_right_latlong[1]
        # self.mpl_extent = [min(longs),
        #                 max(longs),
        #                 min(lats),
        #                 max(lats)]
        #
        self.static_map = self.getStaticMap(self.center)
        #
        # self.mpl_origin = 'upper'
        # if self.upper_left_latlong[1] < 0:
        #     self.mpl_origin = 'lower'

    def multipleImages(self, nlats = 0, nlongs = 0):
        half = nlats//2
        y = self.SIZE[1]
        x = self.SIZE[0]
        hd = np.zeros(((nlats+1)*y, (nlongs+1)*x, 3))
        delta = self.lower_right_latlong[0] - self.upper_left_latlong[0]
        j = 0
        for i in range(-half, 0):
            left, right = y*j, (j+1)*y
            new_lat = self.center[0] - (half - j)*delta
            hd[left:right] = self.multipleLongitudes(new_lat, nlongs)
            j += 1

        left, right = y*j, (j+1)*y
        hd[left:right] = self.multipleLongitudes(self.center[0], nlongs)
        j += 1

        for i in range(1, half+1):
            left, right = y*j, (j+1)*y
            new_lat = self.center[0] - (half - j)*delta
            hd[left:right, :] = self.multipleLongitudes(new_lat, nlongs)
            j += 1

        return hd

    def multipleLongitudes(self, lat, nlongs=6):
        halflongs = nlongs//2
        x = self.SIZE[0]
        hd = np.zeros((self.SIZE[1], (nlongs+1)*x, 3))
        delta = self.upper_left_latlong[1] - self.lower_right_latlong[1]
        j = 0
        for i in range(-halflongs, 0):
            left, right = x*j, (j+1)*x
            new_long = self.center[1] + (halflongs - j)*delta
            center = lat, new_long
            hd[:, left:right, :] = self.getStaticMap(center)
            j += 1

        left, right = x*j, (j+1)*x
        hd[:, left:right, :] = self.getStaticMap((lat, self.center[1]))
        j += 1

        for i in range(1, halflongs+1):
            left, right = x*j, (j+1)*x
            new_long = self.center[1] + (halflongs - j)*delta
            center = lat, new_long
            hd[:, left:right, :] = self.getStaticMap(center)
            j += 1

        return hd

    def LatLonToMeters(self, lat, lon):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        mx = lon * self.ORIGIN_SHIFT / 180.0
        my = np.log( np.tan((90 + lat) * np.pi / 360.0 )) / (np.pi / 180.0)

        my = my * self.ORIGIN_SHIFT / 180.0
        return mx, my


    def MetersToPixels(self, mx, my):
        "Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"

        px = (mx + self.ORIGIN_SHIFT) / self.res
        py = (my + self.ORIGIN_SHIFT) / self.res
        return px, py

    def Resolution(self):
        self.res = self.INITIAL_RESOLUTION/(2**self.zoom)

    def PixelsToMeters(self, px, py):
        "Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

        mx = px * self.res - self.ORIGIN_SHIFT
        my = py * self.res - self.ORIGIN_SHIFT
        return mx, my

    def MetersToLatLon(self, mx, my):
        "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

        lon = (mx / self.ORIGIN_SHIFT) * 180.0
        lat = (my / self.ORIGIN_SHIFT) * 180.0

        lat = 180 / np.pi * (2 * np.arctan(np.exp(lat * np.pi / 180.0)) - np.pi / 2.0)
        return lat, lon

    def getLatLong(self, center):
        meters = self.LatLonToMeters(center[0], center[1])
        pixels = self.MetersToPixels(meters[0], meters[1])

        cpx, cpy = pixels
        upper_left = cpy + self.SIZE[1]*0.5, cpx - self.SIZE[0]*0.5
        lower_right = cpy - self.SIZE[1]*0.5, cpx + self.SIZE[0]*0.5

        corners = [upper_left, lower_right]
        for (i, corner) in enumerate(corners):
            meters = self.PixelsToMeters(corner[1], corner[0])
            latlong = self.MetersToLatLon(meters[0], meters[1])
            corners[i] = latlong

        return corners

    def getUrlStaticMap(self, center):
        url = "http://maps.google.com/maps/api/staticmap?"
        if center != None:
            url += "center=%s&"%center
        url += "size=%dx%d&"%(self.SIZE[0], self.SIZE[1]+self.CUTOFF)
        url += "zoom=%d&"%self.zoom
        url += "maptype=%s&"%self.maptype
        url += "sensor=false"
        return url

    def getStaticMap(self, center):
        center = "%f,%f"%(center[0], center[1])
        url = self.getUrlStaticMap(center)
        f = urlopen(url)
        a = plt.imread(f)
        return a[:-self.CUTOFF]

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
        self.Resolution()

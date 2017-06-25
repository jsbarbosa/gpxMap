from routeAnalizer import *

# route = Route(dataWrapper("GPS-data/Loctome-Teusaca_2017-06-18.gpx"))
route = Route(dataWrapper("GPS-data/Loctome-Sopo.gpx"))
myMap = Map(route)

non_stop = route.ceroSpeed()
non_stop.setAltitude(fourierFilter(non_stop.altitude, 25))
non_stop.setSpeed(fourierFilter(non_stop.speed, 25))

non_stop.printImportant()

animationMethod(non_stop, myMap, jump=non_stop.npoints//120, path="Sopo.mp4", dpi=1920/8)

from routeAnalizer import *

route = Route(dataWrapper("GPS-data/Loctome-Teusaca_2017-06-18.gpx"))
# route = Route(dataWrapper("GPS-data/Loctome-Sopo.gpx"))
myMap = Map(route, maptype="satellite")

non_stop = route.ceroSpeed()
non_stop.printImportant()
# dataPlot(non_stop, myMap)

animationMethod(non_stop, myMap, jump=non_stop.npoints//120, path="Teusaca_2017-06-18.gif", dpi=60)

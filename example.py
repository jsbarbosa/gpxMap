import gpxMap

graph = gpxMap.Graphics("Teusaca.gpx")
graph.setMapType('satellite')


jump = graph.getNumberPoints() // (10 * 24) # 10 seconds

graph.animate(jump = jump)

# to save
# graph.animate(jump = jump, path = "Teusaca.mp4")

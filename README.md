# gpxMap
Animate GPS data. Use a gpx file to display your GPS data.

## install
```
pip install gpxMap
```

## example

```
import gpxMap

graph = gpxMap.Graphics("Teusaca.gpx")
graph.setMapType('satellite') # maptypes: roadmap, satellite, terrain, hybrid

jump = graph.getNumberPoints() // (10 * 24) # 10 seconds

graph.animate(jump = jump)
```

## dependencies
- matplotlib
- gpxpy
- pillow

# Results
## Sopo
![Results](https://github.com/jsbarbosa/gpxMap/blob/master/Sopo.gif)

## Teusaca
![Results](https://github.com/jsbarbosa/gpxMap/blob/master/Teusaca.gif)

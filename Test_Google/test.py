from map import *
import matplotlib.pyplot as plt


bogota = 4.707245, -74.081149, 17
first = Map(*bogota)
temp = first.multipleImages(6, 10)
# temp = first.multipleLongitudes(first.center[0])

# latlon1 = first.upper_left_latlong
# latlon2 = first.lower_right_latlong
# rang = latlon2[1] - latlon1[1]
# second = Map(bogota[0], bogota[1] + rang)
# second.static_map.shape
# total = np.zeros((600, 1200, 3))
# total[:, :600, :] = first.static_map
# total[:, 600:, :] = second.static_map

# plt.imshow(temp)
plt.imsave("Temp.png", temp)
plt.show()

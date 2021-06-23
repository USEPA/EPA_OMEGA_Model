# create plot window object
plt = pg.plot()
# define the data
# thetitle = "pyqtgraph plot"
y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
y1 = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18]
x = range(0, 10)

# create plot
# adding legend
plt.addLegend()
# set properties of the label for y axis
plt.setLabel('left', 'Vertical Values', units='y')
# set properties of the label for x axis
plt.setLabel('bottom', 'Horizontal Values', units='s')
# setting window title to the plot window
plt.setTitle("Test Graph", size="20pt")
# plt.setWindowTitle('title')

plt1 = plt.plot(x, y, name='Red', pen=1)
plt2 = plt.plot(x, y1, name='Blue', pen=2)
plt.showGrid(x=True, y=True)
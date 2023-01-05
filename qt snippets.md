```python
# convert to grayscale ( also removes alpha channel)
image_gray = image_colored.convertToFormat(QtGui.QImage.Format_Grayscale8)

# restore alpha
pixmap = QtGui.QPixmap.fromImage(image_gray)  
alpha_mask = pixmap_colored.mask()  
pixmap.setMask(alpha_mask)  
image_gray = pixmap.toImage()

# make only 20% transparent  
pixmap_gray_transparent = QtGui.QPixmap(pixmap_gray.size())  
pixmap_gray_transparent.fill(QtCore.Qt.transparent)  
painter = QtGui.QPainter(pixmap_gray_transparent)  
painter.setOpacity(0.2)  
painter.drawPixmap(0, 0, pixmap_gray)  
painter.end()
```

[[Qt]]
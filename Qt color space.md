A simple widget to show basic [[color space]] conversion in [[Qt]].
Converting between [[sRGB]] and [[linear color space]].
![[Qt color space-1721323691725.jpeg]]
```python
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QImage, QColor, QPixmap


def convert_srgb_to_linear(r, g, b):
    """Convert an sRGB color to a linear color space."""

    def srgb_to_linear(c):
        c /= 255.0
        return (c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_linear = srgb_to_linear(r)
    g_linear = srgb_to_linear(g)
    b_linear = srgb_to_linear(b)

    return int(r_linear * 255), int(g_linear * 255), int(b_linear * 255)


def convert_linear_to_srgb(r, g, b):
    """Convert a linear RGB color to sRGB."""

    def linear_to_srgb(c):
        c /= 255.0
        return (c * 12.92) if c <= 0.0031308 else (1.055 * (c ** (1 / 2.4)) - 0.055)

    r_srgb = linear_to_srgb(r)
    g_srgb = linear_to_srgb(g)
    b_srgb = linear_to_srgb(b)

    return int(r_srgb * 255), int(g_srgb * 255), int(b_srgb * 255)


def create_colored_image(r, g, b):
    """Create a QImage with the specified color."""
    image = QImage(20, 20, QImage.Format_RGB32)
    image.fill(QColor(r, g, b).rgb())
    return image


def main():
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()

    # Define the sRGB color
    srgb_color = (170, 127, 66)

    # Convert sRGB to linear color space
    linear_color = convert_srgb_to_linear(*srgb_color)
    other_color = convert_linear_to_srgb(*srgb_color)

    # Create QImages for both sRGB and linear colors
    srgb_image = create_colored_image(*srgb_color)
    linear_image = create_colored_image(*linear_color)
    other_image = create_colored_image(*other_color)

    # Convert QImages to QPixmaps and set them on buttons
    srgb_button = QPushButton("sRGB Color")
    srgb_button.setIcon(QPixmap.fromImage(srgb_image))
    srgb_button.setIconSize(srgb_image.size())

    linear_button = QPushButton("Linear Color")
    linear_button.setIcon(QPixmap.fromImage(linear_image))
    linear_button.setIconSize(linear_image.size())

    other_button = QPushButton("other Color")
    other_button.setIcon(QPixmap.fromImage(other_image))
    other_button.setIconSize(linear_image.size())

    # Add buttons to the layout
    layout.addWidget(srgb_button)
    layout.addWidget(linear_button)
    layout.addWidget(other_button)

    # Set layout and show window
    window.setLayout(layout)
    window.show()
    app.setStyle("Fusion")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

[[qt snippets]]
[[Python]]
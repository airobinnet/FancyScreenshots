import sys
import os
import uuid
import configparser
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QIcon, QLinearGradient
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction, QRubberBand, QDesktopWidget, QColorDialog, QCheckBox, QTextBrowser
import random

# Save the options to a secret file so we don't forget them
def save_options_to_config(options):
    config = configparser.ConfigParser()
    config["Options"] = options
    with open("config.ini", "w") as configfile:
        config.write(configfile)

# Load the options from the secret file if it exists
def load_options_from_config():
    options = {}
    config = configparser.ConfigParser()
    if os.path.exists("config.ini"):
        config.read("config.ini")
        options = config["Options"]
    return options

# A draggable icon that you can move around like a pro
class DraggableIcon(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        pixmap = QPixmap("assets/icon.png")
        # set the position to top right
        self.move(QApplication.desktop().screen().rect().topRight() - QPoint(150, -50))
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(self.mask_pixmap(pixmap))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.is_dragging = False
        self.fullscre = None
        self.gradient_colors = (QColor("#f6d365"), QColor("#fda085"))
        self.random_colors = False

        options = load_options_from_config()
        if "gradient_start_color" in options and "gradient_end_color" in options:
            self.gradient_colors = (QColor(options["gradient_start_color"]), QColor(options["gradient_end_color"]))
        if "random_colors" in options:
            self.random_colors = options.getboolean("random_colors")

    # Create a fancy mask for the icon to wear
    def mask_pixmap(self, pixmap):
        masked_pixmap = QPixmap(pixmap.size())
        masked_pixmap.fill(Qt.transparent)
        painter = QPainter(masked_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(pixmap))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(1, 1, 98, 98)
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(3, 3, 94, 94)
        painter.setBrush(QBrush(pixmap))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 90, 90)
        painter.end()
        return masked_pixmap

    # When you press the mouse, remember that we're dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.mouse_offset = event.pos()

    # When you move the mouse, move the icon if we're dragging
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.mouse_offset)

    # When you release the mouse, stop dragging
    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    # When you right click, show the context menu
    def contextMenuEvent(self, event):
        menu = QMenu()
        # Add an action to take a magical screenshot
        menu.addAction(QAction("Take Screenshot", menu))

        # A secret chamber of options lies within
        options_menu = QMenu("Options", menu)
        set_gradient_action = QAction("Set Gradient Colors", options_menu)
        set_gradient_action.triggered.connect(self.set_gradient_colors)
        options_menu.addAction(set_gradient_action)

        # Embrace the chaos of random colors
        random_colors_action = QAction("Random Colors", options_menu, checkable=True)
        random_colors_action.setChecked(self.random_colors)
        random_colors_action.triggered.connect(self.toggle_random_colors)
        options_menu.addAction(random_colors_action)

        menu.addMenu(options_menu)

        # Some self-promotion never hurt anyone
        info_action = QAction("Info", menu)
        info_action.triggered.connect(self.show_info)
        menu.addAction(info_action)

        # A graceful exit for the weary
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        # Let the user choose their destiny
        action = menu.exec_(event.globalPos())
        if action:
            if action.text() == "Take Screenshot":
                self.start_area_selection()

    # What's this info thing all about?
    def show_info(self):
        self.info_window = QWidget()
        self.info_window.setWindowTitle("Info")
        self.info_window.setFixedSize(300, 200)

        info_text_browser = QTextBrowser(self.info_window)
        info_text_browser.setGeometry(10, 10, 280, 180)
        info_text_browser.setOpenExternalLinks(True)
        info_text_browser.setHtml("""
            (c) 2023 AIRobin Solutions<br>
            Under the MIT license<br><br><br>
            <a href="https://airobin.net">https://airobin.net</a><br><br>
            <a href="https://github.com/airobinnet/">https://github.com/airobinnet/</a><br>
        """)

        self.info_window.show()

    # Let's get ready to rumble! Start selecting the area for the screenshot
    def start_area_selection(self):
        if self.fullscre is None:
            self.fullscre = AreaSelector(self)
        self.fullscre.show()

    # Set the gradient colors for the fancy screenshot background
    def set_gradient_colors(self):
        start_color = QColorDialog.getColor()
        if start_color.isValid():
            end_color = QColorDialog.getColor()
            if end_color.isValid():
                self.gradient_colors = (start_color, end_color)
                self.random_colors = False
                options = {
                    "gradient_start_color": start_color.name(),
                    "gradient_end_color": end_color.name(),
                    "random_colors": str(self.random_colors)
                }
                save_options_to_config(options)

    # Toggle the random colors mode for the fancy screenshot background
    def toggle_random_colors(self, checked):
        self.random_colors = checked
        options = {
            "gradient_start_color": self.gradient_colors[0].name(),
            "gradient_end_color": self.gradient_colors[1].name(),
            "random_colors": str(self.random_colors)
        }
        save_options_to_config(options)

# A magical area selector for the perfect screenshot
class AreaSelector(QWidget):
    def __init__(self, draggable_icon, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.rubber_band = None
        self.origin = QPoint()
        self.setWindowState(Qt.WindowFullScreen)
        
        self.draggable_icon = draggable_icon

    # Prepare the screenshot when the area selector is shown
    def showEvent(self, event):
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)

    # Paint the screenshot on the area selector
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.screenshot)

    # When you press the mouse, remember that we're selecting an area
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

    # Update the rubber band as the mouse moves
    def mouseMoveEvent(self, event):
        if self.rubber_band:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    # When you release the mouse, capture the screenshot and close the area selector
    def mouseReleaseEvent(self, event):
        if self.rubber_band:
            self.rubber_band.hide()
            selected_area = self.rubber_band.geometry()
            self.capture_screenshot(selected_area)
            self.rubber_band = None
            self.close()

    # Capture the screenshot and save it as a fancy image
    def capture_screenshot(self, area):
        selected_screenshot = self.screenshot.copy(area)
        fancy_screenshot = self.create_fancy_screenshot(selected_screenshot,
                                                        self.draggable_icon.gradient_colors,
                                                        self.draggable_icon.random_colors)
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        fancy_screenshot.save("screenshots/{}.png".format(uuid.uuid4().hex))

    # Draw a drop shadow around the screenshot to make it look cooler
    def draw_drop_shadow(self, painter, rect):
        shadow_color = QColor(0, 0, 0, 80)
        shadow_radius = 5
        shadow_offset = QPoint(5, 5)

        shadow_rect = rect.translated(shadow_offset)
        for i in range(shadow_radius, 0 , -1):
            shadow_color.setAlpha(80 - (80 * i // shadow_radius))
            painter.setPen(QPen(shadow_color, 1))
            painter.drawRoundedRect(shadow_rect, 20, 20)
            shadow_rect.adjust(0, 0, -1, -1)

    # Turn the ordinary screenshot into a fancy masterpiece
    def create_fancy_screenshot(self, screenshot, gradient_colors=None, random_colors=False):
        larger_side = max(screenshot.width(), screenshot.height())
        bg_width = int(larger_side * 1.25)
        bg_height = int(larger_side * 1.25)
        fancy_screenshot = QPixmap(bg_width, bg_height)
        fancy_screenshot.fill(Qt.transparent)
        painter = QPainter(fancy_screenshot)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the position to center the screenshot
        x = (bg_width - screenshot.width()) // 2
        y = (bg_height - screenshot.height()) // 2

        # Draw rounded corners for the screenshot
        rounded_screenshot = QPixmap(screenshot.size())
        rounded_screenshot.fill(Qt.transparent)
        rounded_painter = QPainter(rounded_screenshot)
        rounded_painter.setRenderHint(QPainter.Antialiasing)
        rounded_painter.setBrush(QBrush(screenshot))
        rounded_painter.setPen(Qt.NoPen)
        rounded_painter.drawRoundedRect(screenshot.rect(), 20, 20)
        rounded_painter.end()

        # Draw drop shadow
        shadow_rect = QRect(x, y, rounded_screenshot.width(), rounded_screenshot.height())
        self.draw_drop_shadow(painter, shadow_rect)

        # Draw screenshot with rounded corners
        painter.drawPixmap(x, y, rounded_screenshot)

        # Draw gradient background
        gradient = QLinearGradient(0, 0, bg_width, bg_height)
        if random_colors:
            start_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            end_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        elif gradient_colors:
            start_color, end_color = gradient_colors
        else:
            start_color = QColor(255, 34, 124, 255)
            end_color = QColor(128, 255, 68, 255)
        gradient.setColorAt(0, start_color)
        gradient.setColorAt(1, end_color)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
        painter.fillRect(0, 0, bg_width, bg_height, gradient)

        painter.end()
        return fancy_screenshot

# Time to unleash the power of the Fancy Screenshot Creator!
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = QWidget()
    window.setWindowTitle('Fancy Screenshot Creator')

    icon = DraggableIcon()
    icon.show()

    sys.exit(app.exec_())

from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets.window.fluent_window import FluentWindowBase, FluentTitleBar


class PureWindow(FluentWindowBase):
    """
    A custom window class inheriting from FluentWindowBase.

    This class provides a simplified structure with a title bar and
    a widget layout. It is designed to manage and organize UI elements
    efficiently, with a resizable title bar and support for dynamic widget
    integration.
    """

    def __init__(self):
        """
        Initializes the PureWindow instance.

        Sets up the title bar, layout structure, and ensures the stacked widget
        is removed for a cleaner layout. Also establishes initial layout margins
        and raises the title bar to the forefront.
        """
        super().__init__()
        self.setTitleBar(FluentTitleBar(self))
        self.widgetLayout = QVBoxLayout()
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1)
        self.stackedWidget.deleteLater()
        self.titleBar.raise_()

    def resizeEvent(self, _):
        """
        Handles the resize event for the window.

        Adjusts the title bar's position and width dynamically based
        on the window's current size.
        """
        self.titleBar.move(20, 0)
        self.titleBar.resize(self.width() - 20, self.titleBar.height())

    def setWidget(self, widget):
        """
        Adds a widget to the layout.

        Args:
            widget: The QWidget instance to be added to the layout.
        """
        self.widgetLayout.addWidget(widget)

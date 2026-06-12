from __future__ import annotations

from PySide6.QtCore import QRect, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from recognize.models.config import Region


class RegionOverlay(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.region_rect = QRect()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def show_region(self, region: Region, duration_ms: int = 1600) -> None:
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())
        self.region_rect = self._to_logical_rect(region)
        self.show()
        self.raise_()
        QTimer.singleShot(duration_ms, self.hide)

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        if self.region_rect.isNull():
            return

        painter = QPainter(self)
        local_rect = QRect(
            self.mapFromGlobal(self.region_rect.topLeft()),
            self.mapFromGlobal(self.region_rect.bottomRight()),
        ).normalized()

        painter.setPen(QPen(QColor(32, 136, 255), 3))
        painter.setBrush(QColor(32, 136, 255, 24))
        painter.drawRoundedRect(local_rect, 8, 8)

        label_rect = QRect(local_rect.x(), max(0, local_rect.y() - 34), 260, 28)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(32, 136, 255, 220))
        painter.drawRoundedRect(label_rect, 6, 6)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(label_rect.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, "当前识别区域")

    def _to_logical_rect(self, region: Region) -> QRect:
        screen = QApplication.primaryScreen()
        ratio = screen.devicePixelRatio()
        geometry = screen.geometry()
        return QRect(
            round(region.x / ratio + geometry.x()),
            round(region.y / ratio + geometry.y()),
            round(region.width / ratio),
            round(region.height / ratio),
        )

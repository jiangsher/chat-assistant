from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, QRect, Signal, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from recognize.models.config import Region

LOGGER = logging.getLogger(__name__)


class RegionSelector(QWidget):
    region_selected = Signal(Region)
    selection_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.start_pos: QPoint | None = None
        self.current_rect = QRect()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.start_pos = event.globalPosition().toPoint()
        self.current_rect = QRect(self.start_pos, self.start_pos)
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.start_pos is None:
            return

        end_pos = event.globalPosition().toPoint()
        self.current_rect = QRect(self.start_pos, end_pos).normalized()
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self.start_pos is None:
            return

        rect = self.current_rect.normalized()
        self.start_pos = None
        self.hide()

        if rect.width() >= 20 and rect.height() >= 20:
            region = self._to_physical_region(rect)
            LOGGER.info("region_selected logical=%s physical=%s", rect, region)
            self.region_selected.emit(region)
        self.selection_finished.emit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.selection_finished.emit()
        super().closeEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        if not self.current_rect.isNull():
            local_rect = QRect(
                self.mapFromGlobal(self.current_rect.topLeft()),
                self.mapFromGlobal(self.current_rect.bottomRight()),
            ).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(local_rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(32, 136, 255), 2))
            painter.drawRect(local_rect)

    def _to_physical_region(self, rect: QRect) -> Region:
        screen = QApplication.screenAt(rect.center()) or QApplication.primaryScreen()
        geometry = screen.geometry()
        ratio = screen.devicePixelRatio()

        x = round((rect.x() - geometry.x()) * ratio + geometry.x() * ratio)
        y = round((rect.y() - geometry.y()) * ratio + geometry.y() * ratio)
        width = round(rect.width() * ratio)
        height = round(rect.height() * ratio)

        return Region(x=x, y=y, width=width, height=height)

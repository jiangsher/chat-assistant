from __future__ import annotations

import logging
import time
from ctypes import windll

from PySide6.QtCore import QPoint, QRect, QSize, QThread, QTimer, Signal, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from recognize.capture.screen_capture import CapturedImage
from recognize.capture.screen_capture import ScreenCapture
from recognize.models.config import Region
from recognize.models.recognition_result import CandidateCard
from recognize.models.recognition_result import RecognitionResult
from recognize.recognition.card_labels import title_label_for_card
from recognize.recognition.formatting import (
    format_debug_info,
    format_unread_cards_for_copy,
    unread_cards,
)
from recognize.recognition.ocr_engine import RapidOcrEngine
from recognize.recognition.page_signature import (
    PageSignature,
    build_page_signature,
    page_signature_changed,
)
from recognize.recognition.pipeline import RecognitionPipeline
from recognize.recognition.unread_detector import UnreadDetector
from recognize.storage.config_store import ConfigStore
from recognize.ui.region_overlay import RegionOverlay
from recognize.ui.region_selector import RegionSelector
from recognize.ui.styles import FLOATING_WINDOW_STYLESHEET

LOGGER = logging.getLogger(__name__)


class ClickableCard(QFrame):
    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class RefreshWorker(QThread):
    result_ready = Signal(object)
    failed = Signal(object, str)

    def __init__(self, pipeline: RecognitionPipeline, captured: CapturedImage) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.captured = captured
        self.region = captured.region

    def run(self) -> None:
        try:
            self.result_ready.emit(self.pipeline.run_captured(self.captured))
        except Exception as exc:  # pragma: no cover - exercised through UI
            LOGGER.exception("refresh_worker_failed region=%s", self.region)
            self.failed.emit(self.region, str(exc))


class FloatingWindow(QWidget):
    def __init__(self, config_store: ConfigStore) -> None:
        super().__init__()
        self.config_store = config_store
        self.config = self.config_store.load()
        self.config.selected_region = None
        self.current_region: Region | None = None
        self.current_page_signature: PageSignature | None = None
        self.last_result: RecognitionResult | None = None
        self.last_output_text = ""
        self.refresh_worker: RefreshWorker | None = None
        self.refresh_started_at: float | None = None
        self.refresh_timeout_ms = 10000
        self.capture_in_progress = False
        self.capture_hidden_opacity = 1.0
        self.capture_delay_ms = 120
        self.selection_previous_opacity = 1.0
        self.source_click_restore_ms = 180
        self.paused = False
        self.pipeline = RecognitionPipeline(
            capture=ScreenCapture(),
            ocr_engine=RapidOcrEngine(),
            unread_detector=UnreadDetector(),
        )

        self.status_label = QLabel("未选择区域")
        self.count_label = QLabel("未读：-")
        self.contact_count_label = QPushButton("联系人：-")
        self.updated_label = QLabel("更新：-")
        self.list_widget = QListWidget()
        self.list_widget.setWordWrap(True)
        self.list_widget.setSpacing(8)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.refresh_button = QPushButton("刷新")
        self.pause_button = QPushButton("暂停")
        self.region_button = QPushButton("选择区域")
        self.copy_button = QPushButton("复制")
        self.debug_button = QPushButton("调试")
        self.region_selector: RegionSelector | None = None
        self.region_overlay = RegionOverlay()

        self._build_ui()
        self._restore_window()
        self._show_waiting_for_region()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_once)
        self.timer.start(self.config.refresh_interval_ms)
        self.refresh_timeout_timer = QTimer(self)
        self.refresh_timeout_timer.setSingleShot(True)
        self.refresh_timeout_timer.timeout.connect(self._on_refresh_timeout)

    def _build_ui(self) -> None:
        flags = (
            Qt.WindowType.Window
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        if self.config.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowTitle("聊天助手")

        title_label = QLabel("聊天助手")
        title_label.setObjectName("WindowTitle")
        self.status_label.setObjectName("StatusPill")
        self.count_label.setObjectName("StatCard")
        self.contact_count_label.setObjectName("StatCard")
        self.updated_label.setObjectName("StatCard")
        self.count_label.setMinimumWidth(120)
        self.contact_count_label.setMinimumWidth(130)
        self.updated_label.setMinimumWidth(150)
        self.contact_count_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.contact_count_label.setCursor(Qt.CursorShape.ArrowCursor)

        self.region_button.setObjectName("PrimaryButton")
        for button in (
            self.pause_button,
            self.refresh_button,
            self.copy_button,
            self.debug_button,
        ):
            button.setObjectName("SecondaryButton")

        self.region_button.setToolTip("选择当前页面要识别的列表区域")
        self.pause_button.setToolTip("暂停或继续自动刷新")
        self.refresh_button.setToolTip("立即重新识别当前区域")
        self.copy_button.setToolTip("复制当前未读结果")
        self.debug_button.setToolTip("显示或隐藏调试信息")

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        header_row.addWidget(title_label)
        header_row.addWidget(self.status_label)
        header_row.addStretch()

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.addWidget(self.region_button)
        top_row.addWidget(self.pause_button)
        top_row.addWidget(self.refresh_button)
        top_row.addWidget(self.copy_button)
        top_row.addWidget(self.debug_button)

        stats_frame = QFrame()
        stats_frame.setObjectName("StatsBar")
        stats_row = QHBoxLayout()
        stats_row.setContentsMargins(6, 4, 6, 4)
        stats_row.setSpacing(4)
        stats_row.addWidget(self.count_label)
        stats_row.addWidget(self.contact_count_label)
        stats_row.addWidget(self.updated_label)
        stats_frame.setLayout(stats_row)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(header_row)
        layout.addWidget(stats_frame)
        layout.addLayout(top_row)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self._apply_styles()
        self._apply_icons()

        self.refresh_button.clicked.connect(self.refresh_once)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.region_button.clicked.connect(self.select_region)
        self.copy_button.clicked.connect(self.copy_unread_results)
        self.debug_button.clicked.connect(self.toggle_debug_mode)
        self._sync_debug_button()

    def _apply_icons(self) -> None:
        icon_size = QSize(18, 18)
        self.contact_count_label.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
        )
        self.refresh_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.copy_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        self.debug_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        self.pause_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        )
        for button in (
            self.contact_count_label,
            self.pause_button,
            self.refresh_button,
            self.copy_button,
            self.debug_button,
        ):
            button.setIconSize(icon_size)

    def _restore_window(self) -> None:
        self.resize(self.config.window_width, self.config.window_height)
        self.move(self.config.window_x, self.config.window_y)

    def _apply_styles(self) -> None:
        self.setStyleSheet(FLOATING_WINDOW_STYLESHEET)

    def _set_status(self, text: str, state: str = "neutral") -> None:
        self.status_label.setText(text)
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _set_stats(
        self,
        unread: int | str = "-",
        contacts: int | str = "-",
        updated: str = "-",
    ) -> None:
        self.count_label.setText(f"未读：{unread}")
        self.contact_count_label.setText(f"联系人：{contacts}")
        self.updated_label.setText(f"更新：{updated}")

    def _add_widget_item(self, widget: QWidget) -> None:
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def _make_wrapped_label(self, text: str, object_name: str = "") -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        if object_name:
            label.setObjectName(object_name)
        return label

    def _add_info_card(
        self,
        title: str,
        body: str = "",
        variant: str = "info",
    ) -> None:
        card = QFrame()
        card.setObjectName("InfoCard")
        card.setProperty("variant", variant)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        title_label = self._make_wrapped_label(title, "InfoTitle")
        if not body:
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        if body:
            body_label = self._make_wrapped_label(body, "InfoBody")
            layout.addWidget(body_label)
        self._add_widget_item(card)

    def _add_unread_card(self, card: CandidateCard) -> None:
        frame = ClickableCard()
        frame.setObjectName("ResultCard")
        frame.clicked.connect(lambda selected_card=card: self.open_source_card(selected_card))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(8)
        unread_text = f"未读 {card.unread_badge}" if card.unread_badge else "未读"
        badge = QLabel(unread_text)
        badge.setObjectName("UnreadBadge")
        header.addWidget(badge)

        name = self._make_wrapped_label(card.name or "未命名", "CardName")
        header.addWidget(name, 1)

        if card.time:
            time_label = QLabel(card.time)
            time_label.setObjectName("CardTime")
            header.addWidget(time_label)
        layout.addLayout(header)

        if card.title:
            field_row = QHBoxLayout()
            field_row.setSpacing(8)
            field_row.setContentsMargins(0, 0, 0, 0)
            field_label = QLabel(title_label_for_card(card))
            field_label.setObjectName("FieldLabel")
            field_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            field_row.addWidget(field_label)
            field_value = self._make_wrapped_label(card.title, "FieldValue")
            field_row.addWidget(field_value, 1)
            layout.addLayout(field_row)

        if card.summary:
            summary = self._make_wrapped_label(f"消息：{card.summary}", "SummaryText")
            layout.addWidget(summary)

        self._add_widget_item(frame)

    def open_source_card(self, card: CandidateCard) -> None:
        if self.capture_in_progress or (
            self.refresh_worker is not None and self.refresh_worker.isRunning()
        ):
            self._set_status("识别中，稍后再点", "warning")
            return

        if self.current_region is None or self.last_result is None:
            self._set_status("请先选择区域", "warning")
            return

        point = self._source_click_point(card)
        if point is None:
            self._set_status("无法定位原列表", "warning")
            return

        self.region_overlay.hide()
        self.hide()
        QTimer.singleShot(80, lambda target=point: self._click_source_point(target))

    def _source_click_point(self, card: CandidateCard) -> QPoint | None:
        if self.current_region is None:
            return None

        x0, y0, x1, y1 = card.bbox
        if x1 <= x0 or y1 <= y0:
            return None

        width = x1 - x0
        safe_offset = min(72, max(24, width // 4))
        physical_x = self.current_region.x + x0 + safe_offset
        physical_y = self.current_region.y + round((y0 + y1) / 2)
        return self._physical_to_logical_point(physical_x, physical_y)

    def _physical_to_logical_point(self, physical_x: int, physical_y: int) -> QPoint:
        for screen in QApplication.screens():
            geometry = screen.geometry()
            ratio = screen.devicePixelRatio()
            physical_rect = QRect(
                round(geometry.x() * ratio),
                round(geometry.y() * ratio),
                round(geometry.width() * ratio),
                round(geometry.height() * ratio),
            )
            if physical_rect.contains(QPoint(physical_x, physical_y)):
                return QPoint(
                    round((physical_x - physical_rect.x()) / ratio + geometry.x()),
                    round((physical_y - physical_rect.y()) / ratio + geometry.y()),
                )

        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        ratio = screen.devicePixelRatio()
        return QPoint(
            round(physical_x / ratio + geometry.x()),
            round(physical_y / ratio + geometry.y()),
        )

    def _click_source_point(self, point: QPoint) -> None:
        QCursor.setPos(point)
        self._send_left_click()
        QTimer.singleShot(self.source_click_restore_ms, self._restore_after_source_click)

    def _send_left_click(self) -> None:
        windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        windll.user32.mouse_event(0x0004, 0, 0, 0, 0)

    def _restore_after_source_click(self) -> None:
        self.show()
        if self.config.always_on_top:
            self.raise_()

    def _add_debug_card(
        self,
        result: RecognitionResult,
        page_signature: PageSignature | None,
    ) -> None:
        card = QFrame()
        card.setObjectName("DebugCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        layout.addWidget(self._make_wrapped_label("调试信息", "DebugTitle"))
        layout.addWidget(
            self._make_wrapped_label(format_debug_info(result, page_signature), "DebugText")
        )
        self._add_widget_item(card)

    def closeEvent(self, event) -> None:  # noqa: N802
        geometry = self.geometry()
        self.config.window_x = geometry.x()
        self.config.window_y = geometry.y()
        self.config.window_width = geometry.width()
        self.config.window_height = geometry.height()
        self.config.selected_region = None
        self.config_store.save(self.config)
        super().closeEvent(event)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.setText("继续" if self.paused else "暂停")
        self.pause_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_MediaPlay
                if self.paused
                else QStyle.StandardPixmap.SP_MediaPause
            )
        )
        if self.paused:
            self._set_status("已暂停", "warning")
        elif self.current_region is None:
            self._show_waiting_for_region()
        else:
            self._set_status("准备就绪", "active")

    def toggle_debug_mode(self) -> None:
        self.config.debug_mode = not self.config.debug_mode
        self.config_store.save(self.config)
        self._sync_debug_button()
        if self.last_result is not None:
            self._render_result(self.last_result)

    def copy_unread_results(self) -> None:
        if not self.last_output_text:
            self._set_status("暂无可复制结果", "warning")
            return

        QApplication.clipboard().setText(self.last_output_text)
        self._set_status("已复制", "success")

    def select_region(self) -> None:
        self._dim_for_region_selection()
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.set_region)
        self.region_selector.selection_finished.connect(self._restore_after_region_selection)
        self.region_selector.showFullScreen()

    def set_region(self, region: Region) -> None:
        self._restore_after_region_selection()
        self.current_region = region
        self.current_page_signature = None
        self.config.selected_region = None
        self.config_store.save(self.config)
        self._set_status("已选择区域", "active")
        self.list_widget.clear()
        self._add_info_card(
            "已选择当前页面区域",
            f"区域：{region.x},{region.y} {region.width}x{region.height}。"
            "更换页面后请重新点击“选择区域”。",
        )
        self.region_overlay.show_region(region)
        self.refresh_once()

    def _dim_for_region_selection(self) -> None:
        self.selection_previous_opacity = self.windowOpacity()
        self.setWindowOpacity(0.12)
        self._set_status("选择区域中", "active")

    def _restore_after_region_selection(self) -> None:
        self.setWindowOpacity(self.selection_previous_opacity or 1.0)

    def refresh_once(self) -> None:
        if self.paused:
            return

        if self.current_region is None:
            self._show_waiting_for_region()
            return

        if self.capture_in_progress:
            return

        if self.refresh_worker is not None and self.refresh_worker.isRunning():
            return

        region = self.current_region
        self.refresh_started_at = time.perf_counter()
        self._set_status("识别中", "active")
        self.refresh_button.setEnabled(False)
        self._begin_capture_without_overlay(region)

    def _begin_capture_without_overlay(self, region: Region) -> None:
        self.capture_in_progress = True
        self.capture_hidden_opacity = self.windowOpacity()
        self.region_overlay.hide()
        self.hide()
        QTimer.singleShot(
            self.capture_delay_ms,
            lambda selected_region=region: self._capture_region(selected_region),
        )

    def _capture_region(self, region: Region) -> None:
        try:
            captured = self.pipeline.capture.capture(region)
        except Exception as exc:
            LOGGER.exception("capture_failed region=%s", region)
            self._restore_after_capture()
            self._on_refresh_failed(region, str(exc))
            self._on_refresh_finished()
            return

        self._restore_after_capture()
        if self.current_region is None or self.current_region != region:
            self._on_refresh_finished()
            return

        self.refresh_worker = RefreshWorker(self.pipeline, captured)
        self.refresh_worker.result_ready.connect(self._on_refresh_result)
        self.refresh_worker.failed.connect(self._on_refresh_failed)
        self.refresh_worker.finished.connect(self._on_refresh_finished)
        self.refresh_worker.start()
        self.refresh_timeout_timer.start(self.refresh_timeout_ms)

    def _restore_after_capture(self) -> None:
        self.capture_in_progress = False
        self.setWindowOpacity(self.capture_hidden_opacity or 1.0)
        self.show()
        if self.config.always_on_top:
            self.raise_()

    def _on_refresh_result(self, result: RecognitionResult) -> None:
        if self.current_region is None or result.region != self.current_region:
            return
        self._stop_refresh_timeout()
        try:
            self._render_result(result)
        except Exception as exc:
            LOGGER.exception("render_result_failed region=%s", result.region)
            self._set_status("渲染失败", "error")
            self.list_widget.clear()
            self._add_info_card("结果渲染失败", str(exc), "error")

    def _on_refresh_failed(self, region: Region, message: str) -> None:
        self._stop_refresh_timeout()
        LOGGER.error(
            "refresh_failed region=%s elapsed_ms=%s message=%s",
            region,
            self._refresh_elapsed_ms(),
            message,
        )
        if self.current_region == region:
            self._set_status("识别失败", "error")
            self.list_widget.clear()
            self._add_info_card("识别失败", message, "error")

    def _on_refresh_finished(self) -> None:
        elapsed_ms = self._refresh_elapsed_ms()
        if elapsed_ms is not None:
            LOGGER.info("refresh_finished elapsed_ms=%s", elapsed_ms)
        self.refresh_button.setEnabled(True)
        self.refresh_worker = None
        self.refresh_started_at = None

    def _on_refresh_timeout(self) -> None:
        if self.refresh_worker is None or not self.refresh_worker.isRunning():
            return

        elapsed_ms = self._refresh_elapsed_ms()
        LOGGER.warning("refresh_timeout elapsed_ms=%s", elapsed_ms)
        self.refresh_button.setEnabled(True)
        self._set_status("识别较慢", "warning")
        self.list_widget.clear()
        self._add_info_card(
            "识别耗时较长",
            "请缩小区域或重新选择区域。后台识别完成后，仍会自动更新结果。",
            "warning",
        )

    def _stop_refresh_timeout(self) -> None:
        if self.refresh_timeout_timer.isActive():
            self.refresh_timeout_timer.stop()

    def _refresh_elapsed_ms(self) -> int | None:
        if self.refresh_started_at is None:
            return None
        return round((time.perf_counter() - self.refresh_started_at) * 1000)

    def _render_result(self, result: RecognitionResult) -> None:
        elapsed_ms = self._refresh_elapsed_ms()
        LOGGER.info(
            "refresh_ok region=%s elapsed_ms=%s raw_blocks=%s cards=%s unread=%s preview=%s",
            result.region,
            elapsed_ms,
            len(result.raw_text_blocks),
            len(result.cards),
            result.unread_count,
            " | ".join(block.text for block in result.raw_text_blocks[:8]),
        )

        page_signature = build_page_signature(result.raw_text_blocks)
        if page_signature_changed(self.current_page_signature, page_signature):
            LOGGER.info(
                "page_signature_changed previous=%s current=%s",
                self.current_page_signature,
                page_signature,
            )
            self._show_region_expired()
            return

        if self.current_page_signature is None and page_signature is not None:
            self.current_page_signature = page_signature

        self.last_result = result
        self._set_stats(
            unread=result.unread_count,
            contacts=result.unread_contact_count,
            updated=f"{result.captured_at:%H:%M:%S}",
        )
        self._set_status("已更新", "success")
        self.list_widget.clear()
        self.last_output_text = ""

        if not result.cards:
            self._show_no_cards(result.raw_text_blocks)
            if self.config.debug_mode:
                self._add_debug_card(result, page_signature)
            return

        if len(result.cards) < 5 and len(result.raw_text_blocks) > 20:
            self._add_info_card(
                "解析提示",
                "提示：当前只解析出少量卡片。若列表里还有更多候选人，"
                "请把识别区域向下拉到列表底部，并避开左侧导航和聊天详情区。",
                "warning",
            )

        visible_unread_cards = unread_cards(result)
        if not visible_unread_cards:
            self._add_info_card(
                "当前没有未读信息",
                "识别区域内没有需要展示的未读联系人。已读卡片会被自动隐藏。",
            )
            if self.config.debug_mode:
                self._add_debug_card(result, page_signature)
            return

        self.last_output_text = format_unread_cards_for_copy(result)
        for card in visible_unread_cards:
            self._add_unread_card(card)

        if self.config.debug_mode:
            self._add_debug_card(result, page_signature)

    def _show_waiting_for_region(self) -> None:
        self._set_stats()
        self._set_status("未选择区域", "neutral")
        self.list_widget.clear()
        self.last_result = None
        self.last_output_text = ""
        self._add_info_card(
            "点击“选择区域”，框选当前页面所需识别的列表",
        )

    def _show_region_expired(self) -> None:
        self.current_region = None
        self.current_page_signature = None
        self.last_result = None
        self.last_output_text = ""
        self._set_stats()
        self._set_status("需重新选择", "warning")
        self.list_widget.clear()
        self._add_info_card(
            "页面可能已变化",
            "检测到当前识别区域可能已经切换到其他页面。为避免把旧区域误当成新页面，"
            "请点击“选择区域”重新框选当前列表。",
            "warning",
        )

    def _show_no_cards(self, raw_text_blocks) -> None:
        if raw_text_blocks:
            preview = "\n".join(block.text for block in raw_text_blocks[:8] if block.text)
            hint = self._diagnose_raw_ocr(raw_text_blocks)
            self._add_info_card(
                "识别到文字，但没有解析出卡片",
                f"{hint}\n\n原始 OCR 预览：\n{preview}",
                "warning",
            )
        else:
            self._add_info_card(
                "暂无 OCR 结果",
                "请选择包含文字的候选人列表区域。",
                "warning",
            )

    def _diagnose_raw_ocr(self, raw_text_blocks) -> str:
        text = " ".join(block.text for block in raw_text_blocks if block.text)
        codex_words = ("Codex", "recognition", "自动化", "插件", "对话", "新对话")
        boss_words = ("自拍馆", "前台", "日结", "包吃住", "未读", "沟通")
        if any(word in text for word in codex_words):
            return "当前区域疑似选到了 Codex 窗口，请重新框选 BOSS 候选人消息列表。"
        if not any(word in text for word in boss_words):
            return "当前区域不像候选人列表，请重新选择包含姓名、岗位、消息、时间的列表区域。"
        return "请重新选择 BOSS 右侧候选人列表区域，尽量从“全部/未读”下面框到列表底部。"

    def _sync_debug_button(self) -> None:
        self.debug_button.setText("调试开" if self.config.debug_mode else "调试")


def run_floating_window(config_store: ConfigStore, argv: list[str]) -> int:
    app = QApplication(argv)
    window = FloatingWindow(config_store)
    window.show()
    return app.exec()

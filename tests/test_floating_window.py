from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import recognize.ui.floating_window as floating_window
from recognize.models.config import AppConfig, Region
from recognize.models.recognition_result import CandidateCard, RecognitionResult, TextBlock
from recognize.ui.floating_window import FloatingWindow


class FakeConfigStore:
    def __init__(self) -> None:
        self.config = AppConfig()

    def load(self) -> AppConfig:
        return self.config

    def save(self, config: AppConfig) -> None:
        self.config = config


class FakeWorker:
    def __init__(self, running: bool) -> None:
        self.running = running

    def isRunning(self) -> bool:  # noqa: N802
        return self.running


class FakePipeline:
    pass


class FakeAutoCapture:
    def __init__(self) -> None:
        self.calls = 0

    def capture_screen(self):
        self.calls += 1


class FakeAutoPipeline:
    def __init__(self) -> None:
        self.capture = FakeAutoCapture()


def test_window_flags_include_native_minimize_button() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())

    flags = window.windowFlags()

    assert flags & Qt.WindowType.WindowType_Mask == Qt.WindowType.Window
    assert flags & Qt.WindowType.WindowSystemMenuHint
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowCloseButtonHint


def test_waiting_for_region_shows_single_instruction_card() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())

    assert window.list_widget.count() == 1
    widget = window.list_widget.itemWidget(window.list_widget.item(0))
    assert widget is not None
    labels = widget.findChildren(floating_window.QLabel)
    texts = [label.text() for label in labels]
    assert texts == ["点击“自动识别”，自动查找当前页面的消息列表"]


def test_window_uses_compact_workspace_controls() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())

    assert window.findChildren(floating_window.QFrame, "StatsBar")
    assert window.auto_region_button.toolTip()
    assert window.pause_button.toolTip()
    assert window.refresh_button.toolTip()
    assert window.copy_button.toolTip()
    assert window.debug_button.toolTip()


def test_render_result_updates_ui_without_name_error() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.pipeline = FakePipeline()
    region = Region(x=1, y=2, width=300, height=400)
    window.current_region = region
    result = RecognitionResult(
        region=region,
        raw_text_blocks=[TextBlock(text="企业微信 消息", bbox=(0, 0, 100, 30))],
        cards=[
            CandidateCard(
                id="1",
                name="招聘协作群",
                title="候选人已通过初筛，请安排面试。",
                title_label="主题",
                summary="李经理：我已经更新表格。",
                unread=True,
                unread_badge="9",
            )
        ],
    )

    window._render_result(result)

    assert "未读：9" == window.count_label.text()
    assert "联系人：1" == window.contact_count_label.text()
    assert window.status_label.text() == "已更新"
    assert window.list_widget.count() == 1
    rendered_card = window.list_widget.itemWidget(window.list_widget.item(0))
    assert rendered_card is not None
    assert rendered_card.objectName() == "ResultCard"
    assert rendered_card.findChildren(floating_window.QLabel, "UnreadBadge")
    assert rendered_card.findChildren(floating_window.QLabel, "FieldLabel")


def test_source_click_point_uses_card_bbox_inside_selected_region() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.current_region = Region(x=100, y=200, width=400, height=500)
    card = CandidateCard(id="1", name="张先生", bbox=(50, 80, 250, 120))

    point = window._source_click_point(card)

    assert point is not None
    assert point.x() == 200
    assert point.y() == 300


def test_open_source_card_hides_window_and_schedules_click(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.current_region = Region(x=100, y=200, width=400, height=500)
    window.last_result = RecognitionResult(region=window.current_region)
    window.last_output_text = "existing"
    card = CandidateCard(id="1", name="张先生", bbox=(50, 80, 250, 120))
    scheduled = []
    clicked = []
    monkeypatch.setattr(
        floating_window.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )
    monkeypatch.setattr(window, "_click_source_point", lambda point: clicked.append(point))

    window.show()
    window.open_source_card(card)

    assert not window.isVisible()
    assert window.last_output_text == "existing"
    assert scheduled
    scheduled[0][1]()
    assert clicked


def test_refresh_timeout_restores_button_and_shows_hint() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.refresh_worker = FakeWorker(running=True)
    window.refresh_button.setEnabled(False)

    window._on_refresh_timeout()

    assert window.refresh_button.isEnabled()
    assert window.status_label.text() == "识别较慢"
    assert window.list_widget.count() == 1


def test_refresh_failed_stops_timeout_and_shows_error() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    region = Region(x=1, y=2, width=300, height=400)
    window.current_region = region
    window.refresh_timeout_timer.start(1000)

    window._on_refresh_failed(region, "截图失败")

    assert not window.refresh_timeout_timer.isActive()
    assert window.status_label.text() == "识别失败"
    assert window.list_widget.count() == 1


def test_refresh_enters_capture_guard_before_ocr_worker(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    region = Region(x=1, y=2, width=300, height=400)
    window.current_region = region
    scheduled = []
    monkeypatch.setattr(
        floating_window.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )

    window.refresh_once()

    assert window.capture_in_progress
    assert not window.refresh_button.isEnabled()
    assert not window.isVisible()
    assert window.refresh_worker is None
    assert scheduled


def test_refresh_without_region_starts_auto_detection(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.pipeline = FakeAutoPipeline()
    scheduled = []
    monkeypatch.setattr(
        floating_window.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )

    window.refresh_once()

    assert window.capture_in_progress
    assert not window.refresh_button.isEnabled()
    assert not window.auto_region_button.isEnabled()
    assert window.current_region is None
    assert scheduled


def test_auto_detect_failed_restores_waiting_state() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())

    window._on_auto_detect_failed("not found")

    assert window.current_region is None
    assert window.status_label.text() == "自动识别失败"
    assert window.list_widget.count() == 1


def test_result_without_cards_schedules_auto_relocation(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = FloatingWindow(FakeConfigStore())
    window.current_region = Region(x=10, y=20, width=300, height=400)
    scheduled = []
    monkeypatch.setattr(
        floating_window.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )
    result = RecognitionResult(
        region=window.current_region,
        raw_text_blocks=[TextBlock(text="聊天记录", bbox=(20, 20, 100, 48))],
        cards=[],
    )

    window._render_result(result)

    assert window.current_region is None
    assert window.auto_relocate_pending
    assert window.status_label.text() == "重新定位中"
    assert scheduled

from __future__ import annotations


FLOATING_WINDOW_STYLESHEET = """
QWidget {
    background: #f6f8fb;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 14px;
}

QLabel#WindowTitle {
    color: #0f172a;
    font-size: 20px;
    font-weight: 800;
    padding-right: 8px;
}

QLabel#StatusPill {
    background: #edf1f7;
    color: #526071;
    border-radius: 13px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#StatusPill[state="active"] {
    background: #e0edff;
    color: #155eef;
}

QLabel#StatusPill[state="warning"] {
    background: #fff3d6;
    color: #9a5b00;
}

QLabel#StatusPill[state="error"] {
    background: #ffe4e8;
    color: #b42318;
}

QLabel#StatusPill[state="success"] {
    background: #dcfce7;
    color: #166534;
}

QFrame#StatsBar {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 8px;
}

QLabel#StatCard,
QPushButton#StatCard {
    background: transparent;
    border: none;
    color: #334155;
    font-size: 13px;
    font-weight: 700;
    padding: 7px 10px;
    text-align: left;
}

QPushButton#StatCard:hover {
    background: transparent;
    border: none;
}

QPushButton {
    min-height: 28px;
    border-radius: 7px;
    padding: 4px 12px;
    font-weight: 700;
}

QPushButton#PrimaryButton {
    background: #2563eb;
    border: 1px solid #1d4ed8;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background: #1d4ed8;
}

QPushButton#PrimaryButton:pressed {
    background: #1e40af;
}

QPushButton#SecondaryButton {
    background: #ffffff;
    border: 1px solid #d7dee8;
    color: #172033;
}

QPushButton#SecondaryButton:hover {
    border-color: #9fb0c5;
    background: #f8fbff;
}

QPushButton#SecondaryButton:pressed {
    background: #edf4ff;
}

QPushButton:disabled {
    background: #eef2f6;
    color: #98a2b3;
    border-color: #e3e8ef;
}

QListWidget {
    background: transparent;
    border: none;
    outline: 0;
}

QFrame#ResultCard,
QFrame#InfoCard,
QFrame#DebugCard {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 8px;
}

QFrame#ResultCard:hover {
    background: #f8fbff;
    border-color: #93c5fd;
}

QFrame#InfoCard[variant="warning"] {
    background: #fffaf0;
    border-color: #f8d98c;
}

QFrame#InfoCard[variant="error"] {
    background: #fff1f3;
    border-color: #fecdd3;
}

QFrame#DebugCard {
    background: #f8fafc;
    border-color: #cbd5e1;
}

QFrame#ResultCard QLabel#CardName,
QFrame#ResultCard QLabel#CardTime,
QFrame#ResultCard QLabel#FieldValue,
QFrame#ResultCard QLabel#SummaryText,
QFrame#InfoCard QLabel#InfoTitle,
QFrame#InfoCard QLabel#InfoBody,
QFrame#DebugCard QLabel#DebugTitle,
QFrame#DebugCard QLabel#DebugText {
    background: transparent;
}

QLabel#UnreadBadge {
    background: #ef4444;
    color: #ffffff;
    border-radius: 11px;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 9px;
}

QLabel#CardName {
    color: #111827;
    font-size: 16px;
    font-weight: 800;
}

QLabel#CardTime {
    color: #667085;
    font-size: 12px;
}

QLabel#FieldLabel {
    background: #eaf2ff;
    color: #155eef;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 7px;
}

QLabel#FieldValue {
    color: #1f2937;
    font-weight: 700;
}

QLabel#SummaryText,
QLabel#InfoBody,
QLabel#DebugText {
    color: #526071;
}

QLabel#InfoTitle,
QLabel#DebugTitle {
    color: #111827;
    font-weight: 800;
}
"""

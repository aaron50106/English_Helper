"""
英文單字訓練系統 - PyQt5 主程序
實現圖形用戶界面
"""

import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QRadioButton, QButtonGroup, QComboBox,
    QSpinBox, QTextEdit, QTableWidget, QTableWidgetItem, QDialog,
    QMessageBox, QTabWidget, QLineEdit, QFormLayout, QListWidget,
    QListWidgetItem, QProgressBar, QSplitter, QAbstractItemView, QHeaderView,
    QScrollArea, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QThread
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from training_engine import get_training_engine
from data_manager import get_data_manager
from utils.input_new_vocabulary import VocabularyLookupService
from utils.app_logger import get_app_logger


LOGGER = get_app_logger("english_helper.ui")


# ==================== 全域設計系統 ====================
# 字型
FONT_FAMILY = "微軟正黑體"

# 淺淡配色系統（商業級主題）
COLOR_BG = "#F4F7FB"          # 主背景 - 極淺藍灰
COLOR_SURFACE = "#FFFFFF"      # 卡片/面板背景 - 純白
COLOR_PRIMARY = "#7FB3D5"      # 主色 - 淡雅藍
COLOR_PRIMARY_HOVER = "#A9CCE3"  # 主色滑鼠懸停
COLOR_PRIMARY_PRESSED = "#6FA8C7"  # 主色按下
COLOR_TEXT = "#2C3E50"         # 主要文字 - 深藍灰
COLOR_TEXT_SOFT = "#5D6D7E"    # 次要文字
COLOR_BORDER = "#D6DEE8"       # 邊框 - 淺灰藍
COLOR_SUCCESS_BG = "#ABEBC6"   # 正確 - 淡綠
COLOR_SUCCESS_TEXT = "#1E8449" # 正確文字
COLOR_ERROR_BG = "#F5B7B1"     # 錯誤 - 淡紅
COLOR_ERROR_TEXT = "#C0392B"   # 錯誤文字
COLOR_HINT = "#5499C7"         # 提示文字 - 柔和藍

# 全域樣式表（QSS）
GLOBAL_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "{FONT_FAMILY}";
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    background-color: {COLOR_SURFACE};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_SOFT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 14px;
    padding: 12px 28px;
    margin-right: 4px;
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_PRIMARY};
    border-bottom: 3px solid {COLOR_PRIMARY};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLOR_PRIMARY_HOVER};
    color: {COLOR_SURFACE};
}}

QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_SURFACE};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED};
}}

QPushButton:disabled {{
    background-color: #E5EAF0;
    color: #AAB7C4;
}}

QLabel {{
    color: {COLOR_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    background-color: transparent;
}}

QRadioButton {{
    color: {COLOR_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 13px;
    spacing: 8px;
    padding: 4px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
}}

QRadioButton::indicator:unchecked {{
    border: 2px solid {COLOR_BORDER};
    border-radius: 10px;
    background-color: {COLOR_SURFACE};
}}

QRadioButton::indicator:checked {{
    border: 2px solid {COLOR_PRIMARY};
    border-radius: 10px;
    background-color: {COLOR_PRIMARY};
}}

QComboBox, QSpinBox {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 13px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 22px;
}}

QComboBox:hover, QSpinBox:hover {{
    border: 1px solid {COLOR_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_PRIMARY_HOVER};
    selection-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    outline: none;
}}

QProgressBar {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background-color: {COLOR_SURFACE};
    text-align: center;
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    color: {COLOR_TEXT};
    height: 22px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 7px;
}}
"""


# 選項按鈕樣式
OPTION_BTN_DEFAULT = f"""
QPushButton {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 14px;
    border: 2px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
}}
QPushButton:hover {{
    border: 2px solid {COLOR_PRIMARY};
    background-color: #EFF6FC;
}}
QPushButton:disabled {{
    color: {COLOR_TEXT};
}}
"""

OPTION_BTN_CORRECT = f"""
QPushButton {{
    background-color: {COLOR_SUCCESS_BG};
    color: {COLOR_SUCCESS_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 14px;
    border: 2px solid {COLOR_SUCCESS_TEXT};
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
}}
"""

OPTION_BTN_WRONG = f"""
QPushButton {{
    background-color: {COLOR_ERROR_BG};
    color: {COLOR_ERROR_TEXT};
    font-family: "{FONT_FAMILY}";
    font-weight: bold;
    font-size: 14px;
    border: 2px solid {COLOR_ERROR_TEXT};
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
}}
"""


class VocabularyTrainingWidget(QWidget):
    """模組1: 單字訓練頁面"""
    
    def __init__(self):
        super().__init__()
        self.training_engine = get_training_engine()
        self.current_question = None
        self.auto_next_timer = QTimer()
        self.auto_next_timer.timeout.connect(self.next_question)
        self.auto_next_timer.setSingleShot(True)
        self.init_ui()
    
    def init_ui(self):
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        # 訓練模式選擇
        mode_layout = QHBoxLayout()
        mode_label = QLabel("訓練模式：")
        mode_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        self.mode_group = QButtonGroup()
        
        mode_ch2en = QRadioButton("中文 → 英文")
        mode_en2ch = QRadioButton("英文 → 中文")
        mode_mixed = QRadioButton("混合模式")
        mode_mixed.setChecked(True)
        
        self.mode_group.addButton(mode_ch2en, 0)
        self.mode_group.addButton(mode_en2ch, 1)
        self.mode_group.addButton(mode_mixed, 2)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(mode_ch2en)
        mode_layout.addWidget(mode_en2ch)
        mode_layout.addWidget(mode_mixed)
        mode_layout.addStretch()
        
        layout.addLayout(mode_layout)

        self.daily_stats_label = QLabel()
        self.daily_stats_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.daily_stats_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        self.daily_stats_label.setWordWrap(True)
        layout.addWidget(self.daily_stats_label)
        
        # 開始按鈕
        self.start_btn = QPushButton("開始訓練")
        self.start_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.start_training)
        layout.addWidget(self.start_btn)
        
        # 題目顯示區
        question_title = QLabel("題目：")
        question_title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        question_title.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(question_title)
        
        self.question_label = QLabel()
        self.question_label.setFont(QFont(FONT_FAMILY, 22, QFont.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet(
            f"color: {COLOR_TEXT}; background-color: {COLOR_SURFACE}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 24px;"
        )
        self.question_label.setMinimumHeight(90)
        layout.addWidget(self.question_label)
        
        # 提示
        self.hint_label = QLabel()
        self.hint_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.hint_label.setStyleSheet(f"color: {COLOR_HINT};")
        layout.addWidget(self.hint_label)
        
        # 選項按鈕
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        self.option_buttons = []
        for i, label in enumerate(['A', 'B', 'C', 'D']):
            btn = QPushButton()
            btn.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
            btn.setMinimumHeight(48)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)
            btn.clicked.connect(lambda checked, x=label: self.select_option(x))
            self.option_buttons.append(btn)
            options_layout.addWidget(btn)
        
        layout.addLayout(options_layout)
        
        # 反饋區
        self.feedback_label = QLabel()
        self.feedback_label.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setMinimumHeight(50)
        layout.addWidget(self.feedback_label)
        
        # 下一題按鈕
        self.next_btn = QPushButton("下一題")
        self.next_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setEnabled(False)
        layout.addWidget(self.next_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        self._refresh_daily_stats()
    
    def start_training(self):
        mode_id = self.mode_group.checkedId()
        modes = ["ch2en", "en2ch", "mixed"]
        mode = modes[mode_id]
        LOGGER.info("Vocabulary training started mode=%s", mode)
        
        self.current_question = self.training_engine.get_vocabulary_training_question(mode=mode)
        self.display_question()
        self.start_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self._refresh_daily_stats()

    def _refresh_daily_stats(self):
        stats = self.training_engine.data_manager.get_daily_vocab_stats()
        self.daily_stats_label.setText(
            f"今日單字訓練：已作答 {stats['answered']} 題，答對 {stats['correct']} 題，答錯 {stats['wrong']} 題"
        )
    
    def display_question(self):
        if not self.current_question:
            return
        
        self.question_label.setText(self.current_question['prompt'])
        self.hint_label.setText(self.current_question['hint'])
        self.feedback_label.setText("")
        
        for i, option in enumerate(self.current_question['options']):
            self.option_buttons[i].setText(f"{chr(65 + i)})  {option}")
            self.option_buttons[i].setEnabled(True)
            self.option_buttons[i].setStyleSheet(OPTION_BTN_DEFAULT)
    
    def select_option(self, option):
        # 直接比較用戶選擇和正確答案
        correct_option = self.current_question['correct_option']
        is_correct = option.upper() == correct_option.upper()
        
        correct_idx = ord(correct_option) - 65
        user_idx = ord(option) - 65
        
        if is_correct:
            LOGGER.info("Vocabulary answer correct option=%s", option)
            # 正確答案 - 淡綠色顯示並自動推進
            self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_CORRECT)
            self.feedback_label.setText("✓ 正確！")
            self.feedback_label.setStyleSheet(f"color: {COLOR_SUCCESS_TEXT};")
            
            # 禁用所有按鈕
            for btn in self.option_buttons:
                btn.setEnabled(False)
            
            # 0.5秒後自動推進到下一題
            self.auto_next_timer.start(500)
        else:
            LOGGER.info("Vocabulary answer wrong option=%s expected=%s", option, correct_option)
            # 錯誤答案 - 顯示錯誤和正確答案，等待用戶確認
            self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_WRONG)
            self.option_buttons[correct_idx].setStyleSheet(OPTION_BTN_CORRECT)
            
            # 顯示詞語對照
            correct_answer = self.current_question.get('correct_answer', '')
            
            if self.current_question.get('mode') == 'ch2en':
                # 中文→英文
                feedback_text = f"✗ 錯誤！　{correct_answer} : {self.current_question['prompt']}"
            else:
                # 英文→中文
                feedback_text = f"✗ 錯誤！　{self.current_question['prompt']} : {correct_answer}"
            
            self.feedback_label.setText(feedback_text)
            self.feedback_label.setStyleSheet(f"color: {COLOR_ERROR_TEXT};")
            
            # 禁用所有選項按鈕，啟用「下一題」按鈕
            for btn in self.option_buttons:
                btn.setEnabled(False)
            
            self.next_btn.setEnabled(True)

        self.training_engine.data_manager.record_daily_vocab_answer(is_correct)
        self._refresh_daily_stats()
    
    def next_question(self):
        # 停止任何待機的自動推進計時器
        self.auto_next_timer.stop()
        
        self.current_question = self.training_engine.get_vocabulary_training_question(
            mode=["ch2en", "en2ch", "mixed"][self.mode_group.checkedId()]
        )
        LOGGER.info("Vocabulary next question loaded")
        self.display_question()
        
        # 禁用下一題按鈕直到回答
        self.next_btn.setEnabled(False)


class ExamPracticeWidget(QWidget):
    """模組2: 歷屆題目練習頁面"""
    
    def __init__(self):
        super().__init__()
        self.training_engine = get_training_engine()
        self.data_manager = get_data_manager()
        self.current_question = None
        self.practice_questions = []
        self.practice_index = 0
        self.practice_correct = 0
        self.practice_active = False
        self.practice_year = None
        self.practice_type = None
        self._ignore_year_change = False
        self.init_ui()
    
    def init_ui(self):
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        # 篩選條件
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        year_label = QLabel("考試年份：")
        year_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        filter_layout.addWidget(year_label)
        self.year_combo = QComboBox()
        self.year_combo.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        for year in [109, 110, 112, 113, 114]:
            self.year_combo.addItem(str(year))
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        filter_layout.addWidget(self.year_combo)
        
        type_label = QLabel("題型：")
        type_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        filter_layout.addWidget(type_label)
        self.type_combo = QComboBox()
        self.type_combo.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.type_combo.addItem("文意字彙")
        self.type_combo.addItem("綜合測驗")
        filter_layout.addWidget(self.type_combo)

        self.random_order_check = QCheckBox("題序亂數")
        self.random_order_check.setChecked(True)
        filter_layout.addWidget(self.random_order_check)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 開始按鈕
        self.start_btn = QPushButton("開始練習")
        self.start_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.start_practice)
        layout.addWidget(self.start_btn)
        
        # 題目顯示
        question_title = QLabel("題目：")
        question_title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        question_title.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(question_title)
        
        self.question_label = QLabel()
        self.question_label.setFont(QFont(FONT_FAMILY, 15, QFont.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet(
            f"color: {COLOR_TEXT}; background-color: {COLOR_SURFACE}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 20px;"
        )
        self.question_label.setMinimumHeight(80)
        layout.addWidget(self.question_label)
        
        # 選項
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        self.option_buttons = []
        for i, label in enumerate(['A', 'B', 'C', 'D']):
            btn = QPushButton()
            btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
            btn.setMinimumHeight(46)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)
            btn.clicked.connect(lambda checked, x=label: self.select_option(x))
            self.option_buttons.append(btn)
            options_layout.addWidget(btn)
        
        layout.addLayout(options_layout)
        
        # 反饋
        self.feedback_label = QLabel()
        self.feedback_label.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setMinimumHeight(40)
        layout.addWidget(self.feedback_label)
        
        # 下一題
        self.next_btn = QPushButton("下一題")
        self.next_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setEnabled(False)
        layout.addWidget(self.next_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        layout.addWidget(self.progress_bar)

        self.score_label = QLabel("目前成績：0/0")
        self.score_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.score_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(self.score_label)
        
        layout.addStretch()
        self.setLayout(layout)

    def _selected_year(self):
        return int(self.year_combo.currentText())

    def _selected_type(self):
        return self.type_combo.currentText()

    def _set_progress(self):
        total = len(self.practice_questions)
        answered = self.practice_index
        correct = self.practice_correct

        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(min(answered, total))
        self.score_label.setText(f"目前成績：{correct}/{answered} | 進度：{answered}/{total}")

    def _reset_buttons(self):
        for btn in self.option_buttons:
            btn.setEnabled(False)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)
        self.next_btn.setEnabled(False)

    def _load_question(self):
        if self.practice_index >= len(self.practice_questions):
            self.end_practice()
            return

        self.current_question = self.practice_questions[self.practice_index]
        question_type = self.current_question.get('question_type') or self.current_question.get('type') or '未知題型'
        prompt = self.current_question.get('prompt') or self.current_question.get('question', '')
        self.question_label.setText(f"【{self.current_question.get('year', '未知')}年 {question_type}】\n\n{prompt}")
        self.feedback_label.setText("")
        self.feedback_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")

        raw_options = self.current_question.get('options', {})
        if isinstance(raw_options, dict):
            option_list = [
                raw_options.get('A', ''),
                raw_options.get('B', ''),
                raw_options.get('C', ''),
                raw_options.get('D', ''),
            ]
        else:
            option_list = list(raw_options)

        for i, option in enumerate(option_list):
            if option:
                self.option_buttons[i].setText(f"{chr(65 + i)})  {option}")
                self.option_buttons[i].setEnabled(True)
                self.option_buttons[i].setStyleSheet(OPTION_BTN_DEFAULT)
            else:
                self.option_buttons[i].setText(f"{chr(65 + i)})")
                self.option_buttons[i].setEnabled(False)

        self._set_progress()

    def _start_practice_session(self, year=None, q_type=None):
        questions = self.data_manager.filter_exam_questions(year=year, question_type=q_type)
        if not questions:
            self.practice_questions = []
            self.practice_active = False
            self.current_question = None
            self._reset_buttons()
            self.progress_bar.setValue(0)
            self.score_label.setText("目前成績：0/0")
            QMessageBox.warning(self, "提示", "沒有符合條件的題目")
            self.start_btn.setEnabled(True)
            return

        if self.random_order_check.isChecked():
            random.shuffle(questions)
        self.practice_questions = questions
        self.practice_index = 0
        self.practice_correct = 0
        self.practice_active = True
        self.practice_year = year
        self.practice_type = q_type
        self.start_btn.setEnabled(False)
        self.year_combo.setEnabled(True)
        self.type_combo.setEnabled(True)
        self._load_question()

    def _on_year_changed(self):
        if self._ignore_year_change:
            return

        if not self.practice_active:
            return

        new_year = self._selected_year()
        if new_year == self.practice_year:
            return

        reply = QMessageBox.question(
            self,
            "重新開始測驗",
            "切換年份會取消目前練習並依新年份重新開始，是否繼續？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            self._ignore_year_change = True
            try:
                index = self.year_combo.findText(str(self.practice_year))
                if index >= 0:
                    self.year_combo.setCurrentIndex(index)
            finally:
                self._ignore_year_change = False
            return

        self._start_practice_session(year=new_year, q_type=self.practice_type)
    
    def start_practice(self):
        year = self._selected_year()
        q_type = self._selected_type()
        LOGGER.info("Exam practice started year=%s type=%s", year, q_type)
        self._start_practice_session(year=year, q_type=q_type)

    def display_question(self):
        self._load_question()
    
    def select_option(self, option):
        correct_option = self.current_question.get('correct_option')
        LOGGER.info("Exam practice selected option=%s expected=%s", option, correct_option)

        if correct_option in ['A', 'B', 'C', 'D']:
            is_correct = option.upper() == correct_option.upper()
            correct_idx = ord(correct_option) - 65
            user_idx = ord(option) - 65

            if is_correct:
                self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_CORRECT)
                self.feedback_label.setText("✓ 正確！")
                self.feedback_label.setStyleSheet(f"color: {COLOR_SUCCESS_TEXT};")
            else:
                self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_WRONG)
                self.option_buttons[correct_idx].setStyleSheet(OPTION_BTN_CORRECT)
                self.feedback_label.setText(f"✗ 錯誤！正確答案是 {correct_option}")
                self.feedback_label.setStyleSheet(f"color: {COLOR_ERROR_TEXT};")
        else:
            self.feedback_label.setText(f"你的答案：{option}（此題暫無官方答案）")
            self.feedback_label.setStyleSheet(f"color: {COLOR_HINT};")

        if option.upper() == correct_option.upper() if correct_option in ['A', 'B', 'C', 'D'] else False:
            self.practice_correct += 1

        self._set_progress()

        for btn in self.option_buttons:
            btn.setEnabled(False)
        
        self.next_btn.setEnabled(True)
    
    def next_question(self):
        self.practice_index += 1
        LOGGER.info("Exam practice next question index=%s total=%s", self.practice_index, len(self.practice_questions))
        self._load_question()

    def end_practice(self):
        self.practice_active = False
        self.current_question = None
        self._reset_buttons()

        total = len(self.practice_questions)
        if total <= 0:
            self.start_btn.setEnabled(True)
            return

        accuracy = self.practice_correct / total * 100 if total > 0 else 0
        self.question_label.setText("本輪練習已完成")
        self.feedback_label.setText(f"成績：{self.practice_correct}/{total}，正確率：{accuracy:.1f}%")
        self.feedback_label.setStyleSheet(f"color: {COLOR_SUCCESS_TEXT};")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.score_label.setText(f"目前成績：{self.practice_correct}/{total} | 進度：{total}/{total}")
        self.data_manager.add_training_record({
            'completed_at': datetime.now().isoformat(timespec='seconds'),
            'record_type': '歷屆練習',
            'item_name': f"{self.practice_year} 年 {self.practice_type}",
            'total_questions': total,
            'correct_answers': self.practice_correct,
            'accuracy': accuracy,
            'spent_time': 0,
        })
        QMessageBox.information(
            self,
            "練習完成",
            f"本輪練習完成。\n\n總題數：{total}\n正確：{self.practice_correct}\n正確率：{accuracy:.1f}%",
        )

        self.start_btn.setEnabled(True)


class RandomQuizWidget(QWidget):
    """模組3: 隨機出題測驗頁面"""
    
    def __init__(self):
        super().__init__()
        self.training_engine = get_training_engine()
        self.quiz_started = False
        self.auto_next_timer = QTimer()
        self.auto_next_timer.timeout.connect(self.next_question)
        self.auto_next_timer.setSingleShot(True)
        self.init_ui()
    
    def init_ui(self):
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        # 設置區
        settings_layout = QFormLayout()
        settings_layout.setSpacing(12)
        settings_layout.setLabelAlignment(Qt.AlignRight)
        
        self.question_count_combo = QComboBox()
        self.question_count_combo.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        for count in range(5, 51, 5):
            self.question_count_combo.addItem(str(count))
        self.question_count_combo.setCurrentText("10")
        count_label = QLabel("題目數量：")
        count_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        settings_layout.addRow(count_label, self.question_count_combo)

        self.vocab_check = QRadioButton("包含單字訓練")
        self.vocab_check.setChecked(True)
        self.exam_check = QRadioButton("包含歷屆試題")
        self.exam_check.setChecked(True)
        
        check_container = QWidget()
        check_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        check_layout = QVBoxLayout(check_container)
        check_layout.setContentsMargins(0, 0, 0, 0)
        check_layout.setSpacing(8)
        check_layout.addWidget(self.vocab_check)
        check_layout.addWidget(self.exam_check)
        type_label = QLabel("題型選擇：")
        type_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        settings_layout.addRow(type_label, check_container)
        
        layout.addLayout(settings_layout)
        
        # 開始按鈕
        self.start_btn = QPushButton("開始測驗")
        self.start_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.start_quiz)
        layout.addWidget(self.start_btn)

        self.reset_btn = QPushButton("重新測驗")
        self.reset_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.reset_btn.setMinimumHeight(44)
        self.reset_btn.clicked.connect(self.reset_quiz)
        layout.addWidget(self.reset_btn)
        self.reset_btn.setEnabled(False)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        layout.addWidget(self.progress_bar)

        self.score_label = QLabel("目前成績：0/0")
        self.score_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.score_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(self.score_label)
        
        # 題目顯示
        question_title = QLabel("題目：")
        question_title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        question_title.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(question_title)
        
        self.question_label = QLabel()
        self.question_label.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet(
            f"color: {COLOR_TEXT}; background-color: {COLOR_SURFACE}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 20px;"
        )
        self.question_label.setMinimumHeight(80)
        layout.addWidget(self.question_label)
        
        # 選項
        options_layout = QVBoxLayout()
        options_layout.setSpacing(12)
        options_layout.setContentsMargins(0, 4, 0, 0)
        self.option_buttons = []
        for i, label in enumerate(['A', 'B', 'C', 'D']):
            btn = QPushButton()
            btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
            btn.setMinimumHeight(52)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)
            btn.clicked.connect(lambda checked, x=label: self.select_option(x))
            self.option_buttons.append(btn)
            options_layout.addWidget(btn)
        
        layout.addLayout(options_layout)
        
        # 反饋與統計
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.stats_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(self.stats_label)
        
        # 反饋訊息
        self.feedback_label = QLabel()
        self.feedback_label.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setMinimumHeight(40)
        layout.addWidget(self.feedback_label)
        
        # 下一題
        self.next_btn = QPushButton("下一題")
        self.next_btn.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setEnabled(False)
        layout.addWidget(self.next_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def start_quiz(self):
        count = int(self.question_count_combo.currentText())
        
        self.training_engine.start_random_quiz(
            question_count=count,
            include_vocab=self.vocab_check.isChecked(),
            include_exam=self.exam_check.isChecked(),
            seed=None,
        )
        LOGGER.info(
            "Random quiz started from UI count=%s include_vocab=%s include_exam=%s",
            count,
            self.vocab_check.isChecked(),
            self.exam_check.isChecked(),
        )
        
        self.quiz_started = True
        self.display_question()
        self.start_btn.setEnabled(False)
        self.reset_btn.setEnabled(True)
        self.question_count_combo.setEnabled(False)
        self.vocab_check.setEnabled(False)
        self.exam_check.setEnabled(False)
        self.next_btn.setEnabled(False)

    def reset_quiz(self):
        if self.quiz_started:
            reply = QMessageBox.question(
                self,
                "重新測驗",
                "確定要丟棄目前進度並清空測驗，重新設定參數嗎？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.auto_next_timer.stop()
        self.training_engine.reset_session()
        self.quiz_started = False
        self.current_question = None
        self.question_label.setText("")
        self.feedback_label.setText("")
        self.stats_label.setText("")
        self.score_label.setText("目前成績：0/0")
        self.progress_bar.setValue(0)

        for btn in self.option_buttons:
            btn.setText("")
            btn.setEnabled(False)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)

        self.start_btn.setEnabled(True)
        self.reset_btn.setEnabled(False)
        self.question_count_combo.setEnabled(True)
        self.vocab_check.setEnabled(True)
        self.exam_check.setEnabled(True)
    
    def display_question(self):
        if not self.quiz_started:
            return

        question = self.training_engine.get_current_question()
        if not question:
            self.end_quiz()
            return
        
        stats = self.training_engine.get_session_statistics()
        total_questions = max(stats['total_questions'], 1)
        self.progress_bar.setRange(0, total_questions)
        self.progress_bar.setValue(min(stats['answered'], total_questions))
        self.stats_label.setText(f"進度：{stats['answered']}/{stats['total_questions']} | 正確率：{stats['accuracy']:.1f}%")
        self.score_label.setText(f"目前成績：{stats['correct']}/{stats['answered']}")
        
        self.question_label.setText(question['prompt'])
        
        for btn in self.option_buttons:
            btn.setText("")
            btn.setEnabled(False)
            btn.setStyleSheet(OPTION_BTN_DEFAULT)

        for i, option in enumerate(question['options']):
            self.option_buttons[i].setText(f"{chr(65 + i)})  {option}")
            self.option_buttons[i].setEnabled(True)
            self.option_buttons[i].setStyleSheet(OPTION_BTN_DEFAULT)
    
    def select_option(self, option):
        if not self.quiz_started:
            return

        is_correct, feedback = self.training_engine.submit_answer(option)
        LOGGER.info("Random quiz selected option=%s correct=%s", option, is_correct)
        
        # 獲取當前題目（已被推進前的題目）
        current_q = self.training_engine.current_session['questions'][
            self.training_engine.current_question_index - 1]
        correct_option = current_q.get('correct_option')
        user_idx = ord(option) - 65
        has_correct_option = correct_option in ['A', 'B', 'C', 'D']
        correct_idx = ord(correct_option) - 65 if has_correct_option else None
        
        if is_correct:
            # 正確答案 - 淡綠色顯示並自動推進
            self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_CORRECT)
            self.feedback_label.setText("✓ 正確！")
            self.feedback_label.setStyleSheet(f"color: {COLOR_SUCCESS_TEXT};")
            
            # 禁用所有選項按鈕
            for btn in self.option_buttons:
                btn.setEnabled(False)
            
            # 0.5秒後自動推進到下一題
            self.auto_next_timer.start(500)
        else:
            # 錯誤答案 - 顯示淡紅色和正確答案
            if has_correct_option:
                self.option_buttons[correct_idx].setStyleSheet(OPTION_BTN_CORRECT)
            self.option_buttons[user_idx].setStyleSheet(OPTION_BTN_WRONG)
            
            # 顯示對照
            current_q = self.training_engine.current_session['questions'][
                self.training_engine.current_question_index - 1]
            
            # 根據題目類型顯示反饋
            if 'mode' in current_q and current_q['mode'] == 'ch2en':
                # 中文→英文
                correct_answer = current_q.get('correct_answer', '')
                prompt = current_q.get('prompt', '')
                feedback_text = f"✗ 錯誤！　{correct_answer} : {prompt}"
            elif 'mode' in current_q and current_q['mode'] == 'en2ch':
                # 英文→中文
                correct_answer = current_q.get('correct_answer', '')
                prompt = current_q.get('prompt', '')
                feedback_text = f"✗ 錯誤！　{prompt} : {correct_answer}"
            else:
                # 歷屆試題，按原來的方式顯示
                if has_correct_option:
                    feedback_text = f"✗ 錯誤！正確答案是 {current_q['correct_option']}"
                else:
                    feedback_text = "✗ 錯誤！此題暫無官方答案"
            
            self.feedback_label.setText(feedback_text)
            self.feedback_label.setStyleSheet(f"color: {COLOR_ERROR_TEXT};")
            
            # 禁用所有選項按鈕，啟用下一題按鈕
            for btn in self.option_buttons:
                btn.setEnabled(False)
            
            self.next_btn.setEnabled(True)
    
    def next_question(self):
        # 停止任何待機的自動推進計時器
        self.auto_next_timer.stop()
        if not self.quiz_started:
            return

        LOGGER.info("Random quiz next question")
        self.display_question()
    
    def end_quiz(self):
        if not self.quiz_started:
            return

        self.quiz_started = False
        self.auto_next_timer.stop()
        self.next_btn.setEnabled(False)

        session_record = self.training_engine.end_session()
        
        result_msg = f"""
測驗完成！

總題數：{session_record['total_questions']}
正確：{session_record['correct_answers']}
準確率：{session_record['accuracy']:.1f}%
耗時：{session_record['spent_time']:.0f}秒
        """
        
        QMessageBox.information(self, "測驗結果", result_msg)
        
        self.start_btn.setEnabled(True)
        self.reset_btn.setEnabled(False)
        self.question_count_combo.setEnabled(True)
        self.vocab_check.setEnabled(True)
        self.exam_check.setEnabled(True)
        self.score_label.setText("目前成績：0/0")


class VocabularyLookupWorker(QObject):
    """背景查詞工作者，避免阻塞 UI。"""

    finished = pyqtSignal(dict)

    def __init__(self, service, word):
        super().__init__()
        self.service = service
        self.word = word

    def run(self):
        try:
            result = self.service.lookup_word(self.word)
        except Exception as err:
            LOGGER.exception("Lookup worker unexpected error word=%s err=%s", self.word, err)
            result = {"success": False, "error": "查詢流程發生未預期錯誤"}
        self.finished.emit(result)


class InputNewVocabularyWidget(QWidget):
    """模組4: 新增單字（API 查詢）"""

    def __init__(self):
        super().__init__()
        self.data_manager = get_data_manager()
        self.lookup_service = VocabularyLookupService()
        self.lookup_result = None
        self.lookup_thread = None
        self.lookup_worker = None
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        input_layout = QHBoxLayout()
        word_label = QLabel("輸入英文單字：")
        word_label.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("例如: appreciate")
        self.word_input.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        self.word_input.returnPressed.connect(self.query_word)

        self.query_btn = QPushButton("查詢")
        self.query_btn.setMinimumHeight(42)
        self.query_btn.clicked.connect(self.query_word)

        input_layout.addWidget(word_label)
        input_layout.addWidget(self.word_input)
        input_layout.addWidget(self.query_btn)
        layout.addLayout(input_layout)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(12)

        self.english_value = QLineEdit()
        self.english_value.setReadOnly(True)

        self.chinese_input = QLineEdit()
        self.chinese_input.setPlaceholderText("中文翻譯")

        self.pos_input = QLineEdit()
        self.pos_input.setPlaceholderText("詞性，例如 noun/verb")

        form_layout.addRow(QLabel("英文："), self.english_value)
        form_layout.addRow(QLabel("中文："), self.chinese_input)
        form_layout.addRow(QLabel("詞性："), self.pos_input)
        layout.addLayout(form_layout)

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(self.message_label)

        self.add_btn = QPushButton("一鍵加入自訂詞庫")
        self.add_btn.setMinimumHeight(44)
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.add_to_custom_vocab)
        layout.addWidget(self.add_btn)

        manager_label = QLabel("自訂詞庫管理")
        manager_label.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        manager_label.setStyleSheet(f"color: {COLOR_PRIMARY}; padding-top: 8px;")
        layout.addWidget(manager_label)

        manager_hint = QLabel("可直接在表格內修改英文、中文、詞性，修改後按儲存變更。")
        manager_hint.setWordWrap(True)
        manager_hint.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(manager_hint)

        manager_btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("重新整理")
        self.refresh_btn.clicked.connect(self.load_custom_vocab_table)
        manager_btn_layout.addWidget(self.refresh_btn)

        self.save_btn = QPushButton("儲存變更")
        self.save_btn.clicked.connect(self.save_custom_vocab_changes)
        manager_btn_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("刪除選取")
        self.delete_btn.clicked.connect(self.delete_selected_custom_word)
        manager_btn_layout.addWidget(self.delete_btn)

        manager_btn_layout.addStretch()
        layout.addLayout(manager_btn_layout)

        self.custom_table = QTableWidget(0, 3)
        self.custom_table.setHorizontalHeaderLabels([
            "英文", "中文", "詞性"
        ])
        self.custom_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.custom_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.custom_table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.EditKeyPressed
        )
        self.custom_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.custom_table.horizontalHeader().setStretchLastSection(True)
        self.custom_table.verticalHeader().setVisible(False)
        self.custom_table.setAlternatingRowColors(True)
        self.custom_table.setMinimumHeight(240)
        layout.addWidget(self.custom_table)

        layout.addStretch()
        self.setLayout(layout)
        self.load_custom_vocab_table()

    def _set_message(self, text, is_error=False):
        color = COLOR_ERROR_TEXT if is_error else COLOR_SUCCESS_TEXT
        self.message_label.setStyleSheet(f"color: {color};")
        self.message_label.setText(text)

    def query_word(self):
        word = self.word_input.text().strip()
        if not word:
            self._set_message("請先輸入英文單字", is_error=True)
            return

        if self.lookup_thread and self.lookup_thread.isRunning():
            self._set_message("查詢進行中，請稍候...", is_error=True)
            return

        self.query_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self._set_message("查詢中，請稍候...")
        LOGGER.info("Vocabulary lookup requested word=%s", word)

        self.lookup_thread = QThread(self)
        self.lookup_worker = VocabularyLookupWorker(self.lookup_service, word)
        self.lookup_worker.moveToThread(self.lookup_thread)

        self.lookup_thread.started.connect(self.lookup_worker.run)
        self.lookup_worker.finished.connect(self._on_lookup_finished)
        self.lookup_worker.finished.connect(self.lookup_thread.quit)
        self.lookup_worker.finished.connect(self.lookup_worker.deleteLater)
        self.lookup_thread.finished.connect(self.lookup_thread.deleteLater)
        self.lookup_thread.start()

    def _clear_lookup_fields(self):
        self.english_value.clear()
        self.chinese_input.clear()
        self.pos_input.clear()

    def load_custom_vocab_table(self):
        vocab = self.data_manager.get_custom_vocabulary()
        self.custom_table.setRowCount(len(vocab))

        for row_index, word in enumerate(vocab):
            values = [
                word.get('english', ''),
                word.get('chinese', ''),
                word.get('part_of_speech', ''),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.custom_table.setItem(row_index, column_index, item)

        self.custom_table.resizeRowsToContents()
        LOGGER.info("Custom vocabulary table loaded count=%s", len(vocab))

    def _collect_custom_vocab_rows(self):
        rows = []
        seen_english = set()
        core_vocab = {w.get('english', '').strip().lower() for w in self.data_manager.get_vocabulary()}

        for row_index in range(self.custom_table.rowCount()):
            english_item = self.custom_table.item(row_index, 0)
            chinese_item = self.custom_table.item(row_index, 1)
            pos_item = self.custom_table.item(row_index, 2)

            english = english_item.text().strip().lower() if english_item else ""
            chinese = chinese_item.text().strip() if chinese_item else ""
            pos = pos_item.text().strip() if pos_item else ""

            if not english:
                raise ValueError(f"第 {row_index + 1} 列英文不可為空")
            if not chinese:
                raise ValueError(f"第 {row_index + 1} 列中文不可為空")

            if english in seen_english:
                raise ValueError(f"第 {row_index + 1} 列英文重複：{english}")
            if english in core_vocab:
                raise ValueError(f"第 {row_index + 1} 列英文已存在於核心詞庫：{english}")

            seen_english.add(english)
            rows.append({
                'english': english,
                'chinese': chinese,
                'part_of_speech': pos,
            })

        return rows

    def save_custom_vocab_changes(self):
        try:
            rows = self._collect_custom_vocab_rows()
        except ValueError as error:
            self._set_message(str(error), is_error=True)
            LOGGER.warning("Save custom vocabulary blocked: %s", error)
            return

        self.data_manager.replace_custom_vocabulary(rows)
        self._set_message("自訂詞庫已儲存更新")
        LOGGER.info("Custom vocabulary changes saved count=%s", len(rows))
        QMessageBox.information(self, "完成", "自訂詞庫已更新")

    def delete_selected_custom_word(self):
        selected_rows = self.custom_table.selectionModel().selectedRows()
        if not selected_rows:
            self._set_message("請先選取要刪除的單字", is_error=True)
            return

        row_index = selected_rows[0].row()
        english_item = self.custom_table.item(row_index, 0)
        english = english_item.text().strip() if english_item else ""
        confirm = QMessageBox.question(
            self,
            "確認刪除",
            f"確定要刪除自訂單字：{english or row_index + 1}？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        self.data_manager.delete_custom_word(row_index)
        self.load_custom_vocab_table()
        self._set_message(f"已刪除：{english or row_index + 1}")
        LOGGER.info("Custom vocabulary deleted from manager row_index=%s", row_index)

    def _on_lookup_finished(self, result):
        self.query_btn.setEnabled(True)
        self.lookup_thread = None
        self.lookup_worker = None

        if not result.get('success'):
            self.lookup_result = None
            self._clear_lookup_fields()
            self._set_message(result.get('error', '查詢失敗'), is_error=True)
            LOGGER.warning("Vocabulary lookup failed error=%s", result.get('error', ''))
            return

        self.lookup_result = result
        self.english_value.setText(result.get('english', ''))
        self.chinese_input.setText(result.get('chinese', ''))
        self.pos_input.setText(result.get('part_of_speech', ''))
        self.add_btn.setEnabled(True)
        warning = result.get('warning', '')
        if warning:
            self._set_message(f"查詢完成：{warning}")
            LOGGER.warning("Vocabulary lookup warning=%s", warning)
        else:
            self._set_message("查詢完成，可直接加入自訂詞庫")
            LOGGER.info("Vocabulary lookup success word=%s", result.get('english', ''))

    def add_to_custom_vocab(self):
        english = self.english_value.text().strip().lower()
        chinese = self.chinese_input.text().strip()
        pos = self.pos_input.text().strip()

        if not english:
            self._set_message("尚未有可新增的單字，請先查詢", is_error=True)
            LOGGER.warning("Add custom word blocked: no english value")
            return

        if not chinese:
            self._set_message("中文翻譯不可為空", is_error=True)
            LOGGER.warning("Add custom word blocked: missing chinese word=%s", english)
            return

        all_vocab = self.data_manager.get_all_vocabulary()
        if any((w.get('english', '').strip().lower() == english) for w in all_vocab):
            self._set_message("此單字已存在詞庫中", is_error=True)
            LOGGER.warning("Add custom word blocked: duplicate word=%s", english)
            return

        self.data_manager.add_custom_word(
            english=english,
            chinese=chinese,
            pos=pos,
        )

        self.add_btn.setEnabled(False)
        self._set_message(f"已加入自訂詞庫：{english}")
        LOGGER.info("Custom vocabulary saved word=%s", english)
        self.load_custom_vocab_table()
        QMessageBox.information(self, "完成", f"已新增單字：{english}")


class TrainingRecordsWidget(QWidget):
    """模組5: 測驗紀錄查閱頁面"""

    def __init__(self):
        super().__init__()
        self.data_manager = get_data_manager()
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("測驗紀錄")
        title.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        header_layout.addWidget(title)

        self.record_type_combo = QComboBox()
        self.record_type_combo.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.record_type_combo.addItems(["全部紀錄", "隨機測驗", "歷屆練習"])
        self.record_type_combo.currentIndexChanged.connect(self.load_records)
        header_layout.addWidget(self.record_type_combo)

        self.refresh_records_btn = QPushButton("重新整理")
        self.refresh_records_btn.clicked.connect(self.load_records)
        header_layout.addWidget(self.refresh_records_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.summary_label = QLabel("")
        self.summary_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.summary_label.setStyleSheet(f"color: {COLOR_TEXT_SOFT};")
        layout.addWidget(self.summary_label)

        self.records_table = QTableWidget(0, 6)
        self.records_table.setHorizontalHeaderLabels([
            "完成時間", "完成項目", "類型", "題目數量", "正確題數", "正確率"
        ])
        self.records_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.records_table)

        self.setLayout(layout)
        self.load_records()

    def load_records(self):
        selected_type = self.record_type_combo.currentText()
        records = self.data_manager.get_training_records()
        normalized_records = [self.data_manager.normalize_training_record(record) for record in records]

        if selected_type != "全部紀錄":
            normalized_records = [
                record for record in normalized_records
                if record['record_type'] == selected_type
            ]

        self.records_table.setRowCount(len(normalized_records))

        for row_index, record in enumerate(normalized_records):
            values = [
                record['completed_at'],
                record['item_name'],
                record['record_type'],
                str(record['total_questions']),
                str(record['correct_answers']),
                f"{record['accuracy']:.1f}%",
            ]
            for column_index, value in enumerate(values):
                self.records_table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.summary_label.setText(f"共 {len(normalized_records)} 筆紀錄")
        self.records_table.resizeRowsToContents()
        LOGGER.info("Training records loaded count=%s filter=%s", len(normalized_records), selected_type)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("English Master ─ 高中英文單字訓練系統")
        self.setGeometry(100, 100, 1040, 760)
        self.setMinimumSize(900, 680)
        
        # 中央容器
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        central = QWidget()
        central.setMinimumSize(1040, 760)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)
        
        # 頂部標題列
        header = QLabel("English Master")
        header.setFont(QFont(FONT_FAMILY, 24, QFont.Bold))
        header.setStyleSheet(f"color: {COLOR_PRIMARY}; padding: 4px 6px;")
        subtitle = QLabel("高中英文單字訓練系統")
        subtitle.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_SOFT}; padding: 0px 8px 6px 8px;")
        
        main_layout.addWidget(header)
        main_layout.addWidget(subtitle)
        
        # 標籤頁
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setMinimumSize(960, 640)
        
        # 模組1：單字訓練
        tab1 = VocabularyTrainingWidget()
        self.tabs.addTab(tab1, "  單字訓練  ")
        
        # 模組2：歷屆題目
        tab2 = ExamPracticeWidget()
        self.tabs.addTab(tab2, "  歷屆題目練習  ")
        
        # 模組3：隨機測驗
        tab3 = RandomQuizWidget()
        self.tabs.addTab(tab3, "  隨機測驗  ")

        # 模組4：新增單字
        tab4 = InputNewVocabularyWidget()
        self.tabs.addTab(tab4, "  新增單字  ")

        # 模組5：測驗紀錄
        self.records_tab = TrainingRecordsWidget()
        self.tabs.addTab(self.records_tab, "  測驗紀錄  ")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        scroll_area.setWidget(central)
        self.setCentralWidget(scroll_area)

    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.records_tab:
            self.records_tab.load_records()


def main():
    # 初始化數據管理器並加載試題
    data_manager = get_data_manager()
    data_manager.load_exam_questions()
    LOGGER.info("Application startup: exam questions loaded")
    
    app = QApplication(sys.argv)
    
    # 設置全域字體（微軟正黑體，粗體）
    font = QFont(FONT_FAMILY, 10)
    font.setBold(True)
    app.setFont(font)
    
    # 套用全域淺淡主題樣式表
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    window = MainWindow()
    window.show()
    LOGGER.info("Application window shown")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

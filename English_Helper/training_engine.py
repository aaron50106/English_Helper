"""
英文單字訓練系統 - 訓練引擎
實現單字訓練和隨機出題功能
"""

import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from data_manager import get_data_manager
from utils.app_logger import get_app_logger


LOGGER = get_app_logger("english_helper.training")


class TrainingEngine:
    """訓練引擎 - 處理訓練邏輯和出題"""
    
    def __init__(self):
        self.data_manager = get_data_manager()
        self.current_session = None
        self.current_question_index = 0
        LOGGER.info("TrainingEngine initialized")
    
    # =================== 模組1: 單字訓練 ===================
    
    def get_vocabulary_training_question(self, mode: str = "ch2en", rng=None) -> Dict:
        """
        生成單字訓練題目
        mode: "ch2en" (中文→英文) / "en2ch" (英文→中文) / "mixed" (混合)
        """
        # 如果是mixed模式，隨機選擇一種
        rng = rng or random

        if mode == "mixed":
            mode = rng.choice(["ch2en", "en2ch"])
        
        # 獲取所有詞彙
        vocabulary = self.data_manager.get_all_vocabulary()
        if not vocabulary:
            LOGGER.warning("No vocabulary available for training question")
            return None
        
        # 隨機選擇一個單字
        correct_word = rng.choice(vocabulary)
        
        if mode == "ch2en":
            # 中文→英文選擇
            correct_key = correct_word.get('id', correct_word.get('english'))
            question = {
                'type': 'vocabulary',
                'mode': 'ch2en',
                'word_id': correct_key,
                'prompt': correct_word['chinese'],
                'hint': f"詞性：{correct_word.get('part_of_speech', '未知')}",
                'correct_answer': correct_word['english'],
                'correct_option': None,  # 待設置
            }
            
            # 生成選項
            options = [correct_word['english']]
            
            # 添加干擾項（隨機選擇其他單字）
            other_words = [w for w in vocabulary if w.get('english', '') != correct_word.get('english', '')]
            for _ in range(3):
                if other_words:
                    options.append(rng.choice(other_words)['english'])
            
                rng.shuffle(options)
            question['options'] = options
            question['correct_option'] = chr(65 + options.index(correct_word['english']))  # A, B, C, D
            
        else:  # en2ch
            # 英文→中文選擇
            correct_key = correct_word.get('id', correct_word.get('english'))
            question = {
                'type': 'vocabulary',
                'mode': 'en2ch',
                'word_id': correct_key,
                'prompt': correct_word['english'],
                'hint': f"例句：{correct_word.get('example_sentence', '無例句')}",
                'correct_answer': correct_word['chinese'],
                'correct_option': None,
            }
            
            # 生成選項
            options = [correct_word['chinese']]
            
            # 添加干擾項
            other_words = [w for w in vocabulary if w.get('english', '') != correct_word.get('english', '')]
            for _ in range(3):
                if other_words:
                    options.append(rng.choice(other_words)['chinese'])
            
                rng.shuffle(options)
            question['options'] = options
            question['correct_option'] = chr(65 + options.index(correct_word['chinese']))
        
        LOGGER.info("Generated vocabulary question mode=%s word_id=%s", mode, question.get('word_id'))
        return question
    
    # =================== 模組2: 歷屆題目練習 ===================
    
    def get_exam_question(self, year: Optional[int] = None, question_type: Optional[str] = None, rng=None) -> Dict:
        """
        獲取歷屆試題
        year: 篩選年份（如109, 110等）
        question_type: 篩選題型（如"文意字彙"、"綜合測驗"等）
        """
        questions = self.data_manager.filter_exam_questions(year=year, question_type=question_type)
        
        if not questions:
            LOGGER.warning("No exam question found year=%s question_type=%s", year, question_type)
            return None
        
        rng = rng or random
        exam_q = rng.choice(questions)
        exam_question_type = exam_q.get('question_type') or exam_q.get('type') or '未知題型'
        
        output = {
            'type': 'exam',
            'id': exam_q.get('id'),
            'year': exam_q.get('year'),
            'question_type': exam_question_type,
            'prompt': exam_q.get('question', ''),
            'options': [
                exam_q.get('options', {}).get('A', ''),
                exam_q.get('options', {}).get('B', ''),
                exam_q.get('options', {}).get('C', ''),
                exam_q.get('options', {}).get('D', ''),
            ],
            'correct_option': exam_q.get('correct_option'),
        }
        LOGGER.info("Generated exam question year=%s type=%s number=%s", output.get('year'), output.get('question_type'), exam_q.get('number'))
        return output
    
    # =================== 模組3: 隨機出題系統 ===================
    
    def start_random_quiz(self, question_count: int = 10, 
                         include_vocab: bool = True, include_exam: bool = True, seed: Optional[str] = None) -> Dict:
        """
        開始隨機測驗
        """
        rng = random.Random(seed) if seed is not None else random

        if include_vocab and include_exam:
            item_name = "隨機測驗（單字＋歷屆）"
        elif include_vocab:
            item_name = "隨機測驗（單字）"
        else:
            item_name = "隨機測驗（歷屆）"

        self.current_session = {
            'start_time': datetime.now(),
            'questions': [],
            'responses': [],
            'total_questions': question_count,
            'seed': seed,
            'record_type': '隨機測驗',
            'item_name': item_name,
            'types': {
                'vocabulary': include_vocab,
                'exam': include_exam,
            }
        }
        LOGGER.info(
            "Random quiz started total=%s include_vocab=%s include_exam=%s",
            question_count,
            include_vocab,
            include_exam,
        )
        
        # 生成題目列表
        for i in range(question_count):
            # 隨機選擇題型（詞彙或歷屆題目）
            if include_vocab and include_exam:
                q_type = rng.choice(['vocab', 'exam'])
            elif include_vocab:
                q_type = 'vocab'
            else:
                q_type = 'exam'
            
            if q_type == 'vocab':
                # 隨機選擇訓練模式
                mode = rng.choice(['ch2en', 'en2ch'])
                question = self.get_vocabulary_training_question(mode=mode, rng=rng)
            else:
                question = self.get_exam_question(rng=rng)
            
            if question:
                self.current_session['questions'].append(question)
        
        self.current_question_index = 0
        LOGGER.info("Random quiz question pool prepared count=%s", len(self.current_session['questions']))
        return self.get_next_question()
    
    def get_current_question(self) -> Optional[Dict]:
        """取得當前問題"""
        if not self.current_session or self.current_question_index >= len(self.current_session['questions']):
            return None
        return self.current_session['questions'][self.current_question_index]
    
    def get_next_question(self) -> Optional[Dict]:
        """取得下一問題"""
        if not self.current_session:
            return None
        
        if self.current_question_index < len(self.current_session['questions']):
            question = self.current_session['questions'][self.current_question_index]
            return question
        
        return None
    
    def submit_answer(self, user_answer: str) -> Tuple[bool, str]:
        """
        提交答案並立即得到反饋
        user_answer: 用戶選擇的選項 ("A", "B", "C", "D")
        Returns: (是否正確, 反饋信息)
        """
        question = self.get_current_question()
        if not question:
            LOGGER.warning("submit_answer called with no current question")
            return False, "沒有問題"
        
        is_correct = user_answer.upper() == question.get('correct_option', '')
        
        feedback = ""
        if is_correct:
            feedback = f"✓ 正確！"
        else:
            feedback = f"✗ 錯誤！正確答案是 {question['correct_option']}"
        
        # 記錄回答
        self.current_session['responses'].append({
            'question_index': self.current_question_index,
            'user_answer': user_answer.upper(),
            'is_correct': is_correct,
        })
        LOGGER.info(
            "Answer submitted index=%s type=%s user=%s correct=%s",
            self.current_question_index,
            question.get('type'),
            user_answer.upper(),
            is_correct,
        )
        
        self.current_question_index += 1
        return is_correct, feedback
    
    def get_session_statistics(self) -> Dict:
        """取得當前測驗的統計數據"""
        if not self.current_session:
            return {}
        
        responses = self.current_session['responses']
        total = len(responses)
        correct = sum(1 for r in responses if r['is_correct'])
        
        return {
            'total_questions': len(self.current_session['questions']),
            'answered': total,
            'correct': correct,
            'accuracy': correct / total * 100 if total > 0 else 0,
            'duration': (datetime.now() - self.current_session['start_time']).total_seconds(),
        }
    
    def end_session(self) -> Dict:
        """結束測驗並生成報告"""
        if not self.current_session:
            LOGGER.warning("end_session called with no active session")
            return {
                'timestamp': datetime.now().isoformat(),
                'total_questions': 0,
                'correct_answers': 0,
                'accuracy': 0,
                'spent_time': 0,
                'details': [],
            }

        stats = self.get_session_statistics()
        
        session_record = {
            'timestamp': self.current_session['start_time'].isoformat(),
            'completed_at': datetime.now().isoformat(timespec='seconds'),
            'record_type': self.current_session.get('record_type', '隨機測驗'),
            'item_name': self.current_session.get('item_name', '隨機測驗'),
            'total_questions': stats['total_questions'],
            'correct_answers': stats['correct'],
            'accuracy': stats['accuracy'],
            'spent_time': stats['duration'],
            'details': self.current_session['responses'],
        }
        
        self.data_manager.add_training_record(session_record)
        LOGGER.info(
            "Quiz ended total=%s correct=%s accuracy=%.1f",
            session_record['total_questions'],
            session_record['correct_answers'],
            session_record['accuracy'],
        )
        
        self.current_session = None
        self.current_question_index = 0
        
        return session_record

    def reset_session(self):
        """丟棄目前測驗狀態"""
        self.current_session = None
        self.current_question_index = 0
        LOGGER.info("Quiz session reset")


# 全局實例
_training_engine = None


def get_training_engine() -> TrainingEngine:
    """獲取全局訓練引擎實例"""
    global _training_engine
    if _training_engine is None:
        _training_engine = TrainingEngine()
    return _training_engine

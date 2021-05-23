import time
from datetime import datetime


from core.models import HistoryModel


class SpeechHistory:
    def __init__(self, frame_sleep_interval=5, speech_history_interval=40):
        self.sleep_interval = frame_sleep_interval
        self.history_interval = speech_history_interval
        self.conversation_history = []
        self.classification = None

    def set_speech_timer(self):
        return time.time() + self.sleep_interval

    def set_history_timer(self):
        return time.time() + self.history_interval

    def check_hist_timer(self, timer):
        if time.time() >= timer:
            self.save_to_db()
            self.conversation_history = []
            return True
        else:
            return False

    def check_speech_timer(self, timer):
        return True if time.time() >= timer else False

    def set_classification_label(self, label):
        self.classification = label

    def save_to_db(self):
        self.conversation_history = [i + '.\n' for i in self.conversation_history]
        if len(self.conversation_history) > 0:
            temp_cov = ''.join(self.conversation_history)
            hist_model = HistoryModel(history=temp_cov, date_time=str(datetime.now()))
            hist_model.save()

    def insert_in_history(self, classification):
        self.conversation_history.append(classification)

import csv
import copy
import itertools

import pyttsx3
from threading import Thread

import cv2 as cv
import numpy as np
import mediapipe as mp

from Sign2Speech.settings import BASE_DIR
from core.speech_models.speech_history import SpeechHistory

from core.deep_models.drawings import draw_info, draw_landmarks, draw_info_text, draw_bounding_rect
from core.deep_models.utils import CvFpsCalc
from core.deep_models.model.keypoint_classifier.keypoint_classifier import KeyPointClassifier


class ClassifierLoader:
    def __init__(self, use_static_image_mode=False,
                 min_detection_confidence=0.7, min_tracking_confidence=0.5, use_brect=True, speech=False):
        self.use_brect = use_brect
        self.speech = speech
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=use_static_image_mode,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)

        self.keypoint_classifier = KeyPointClassifier()

        label_file_path = str(BASE_DIR) + '\\core\\deep_models\\model\\keypoint_classifier\\labels_alpha.csv'

        with open(label_file_path,
                  encoding='utf-8-sig') as f:
            self.keypoint_classifier_labels = csv.reader(f)
            self.keypoint_classifier_labels = [
                row[0] for row in self.keypoint_classifier_labels
            ]

        self.speech_history = SpeechHistory()
        self.timer = self.speech_history.set_speech_timer()
        self.conversation_timer = self.speech_history.set_history_timer()

    def calc_landmark_list(self, image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_point = []

        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)

            landmark_point.append([landmark_x, landmark_y])

        return landmark_point

    def pre_process_landmark(self, landmark_list):
        temp_landmark_list = copy.deepcopy(landmark_list)

        base_x, base_y = 0, 0
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:
                base_x, base_y = landmark_point[0], landmark_point[1]

            temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
            temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

        temp_landmark_list = list(
            itertools.chain.from_iterable(temp_landmark_list))

        max_value = max(list(map(abs, temp_landmark_list)))

        def normalize_(n):
            return n / max_value

        temp_landmark_list = list(map(normalize_, temp_landmark_list))

        return temp_landmark_list

    def calc_bounding_rect(self, image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_array = np.empty((0, 2), int)

        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)

            landmark_point = [np.array((landmark_x, landmark_y))]

            landmark_array = np.append(landmark_array, landmark_point, axis=0)

        x, y, w, h = cv.boundingRect(landmark_array)

        return [x, y, x + w, y + h]

    def web_presentable_frame(self, frame):
        ret, jpeg = cv.imencode('.jpg', frame)
        return jpeg.tobytes()

    def enable_speech(self):
        self.speech = True

    def disable_speech(self):
        self.speech = False

    def classify(self, frame):

        if self.speech_history.check_hist_timer(self.conversation_timer):
            self.conversation_timer = self.speech_history.set_history_timer()

        frame = cv.flip(frame, 1)

        fps = self.cvFpsCalc.get()

        debug_image = copy.deepcopy(frame)

        image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        image.flags.writeable = False
        results = self.hands.process(image)
        image.flags.writeable = True

        collected_84_set_landmark_list = []

        if results.multi_hand_landmarks:
            if len(results.multi_hand_landmarks) == 1:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                      results.multi_handedness):
                    brect = self.calc_bounding_rect(debug_image, hand_landmarks)

                    landmark_list = self.calc_landmark_list(debug_image, hand_landmarks)
                    pre_processed_landmark_list = self.pre_process_landmark(
                        landmark_list)

                    collected_84_set_landmark_list.append([
                        pre_processed_landmark_list, list(np.zeros_like(pre_processed_landmark_list))
                    ])
                else:
                    hand_one_lm, hand_two_lm = collected_84_set_landmark_list[0]
                    hand_sign_id = self.keypoint_classifier([*hand_one_lm, *hand_two_lm])
                    if self.speech_history.check_speech_timer(self.timer):
                        self.speech_history.set_classification_label(self.keypoint_classifier_labels[hand_sign_id])
                        self.speech_history.insert_in_history(self.keypoint_classifier_labels[hand_sign_id])
                        self.create_speech_thread(self.keypoint_classifier_labels[hand_sign_id])
                    debug_image = draw_bounding_rect(self.use_brect, debug_image, brect)
                    debug_image = draw_landmarks(debug_image, landmark_list)
                    debug_image = draw_info_text(
                        debug_image,
                        brect,
                        handedness,
                        self.keypoint_classifier_labels[hand_sign_id])
                    debug_image = draw_info(debug_image, fps)
                    return debug_image
            elif len(results.multi_hand_landmarks) == 2:
                landmark_list_draw_copy = []
                counter = 0
                points_set_21 = []
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                      results.multi_handedness):
                    landmark_list = self.calc_landmark_list(debug_image, hand_landmarks)
                    pre_processed_landmark_list = self.pre_process_landmark(
                        landmark_list)

                    points_set_21.append([pre_processed_landmark_list])
                    landmark_list_draw_copy.append(hand_landmarks)
                    counter += 1
                else:
                    collected_84_set_landmark_list.append([
                        *points_set_21[0], *points_set_21[1]
                    ])
                    hand_one_lm, hand_two_lm = collected_84_set_landmark_list[0]
                    hand_sign_id = self.keypoint_classifier([*hand_one_lm, *hand_two_lm])
                    if self.speech_history.check_speech_timer(self.timer):
                        self.speech_history.set_classification_label(self.keypoint_classifier_labels[hand_sign_id])
                        self.speech_history.insert_in_history(self.keypoint_classifier_labels[hand_sign_id])
                        self.create_speech_thread(self.keypoint_classifier_labels[hand_sign_id])
                    brect_1 = self.calc_bounding_rect(debug_image, landmark_list_draw_copy[0])
                    brect_2 = self.calc_bounding_rect(debug_image, landmark_list_draw_copy[1])
                    lm_1 = self.calc_landmark_list(debug_image, landmark_list_draw_copy[0])
                    lm_2 = self.calc_landmark_list(debug_image, landmark_list_draw_copy[1])
                    debug_image = draw_bounding_rect(self.use_brect, debug_image, brect_1)
                    debug_image = draw_bounding_rect(self.use_brect, debug_image, brect_2)
                    debug_image = draw_landmarks(debug_image, lm_1)
                    debug_image = draw_landmarks(debug_image, lm_2)
                    debug_image = draw_info_text(debug_image, brect_1, handedness,
                                                 self.keypoint_classifier_labels[hand_sign_id])
                    debug_image = draw_info_text(debug_image, brect_2, handedness,
                                                 self.keypoint_classifier_labels[hand_sign_id])

                    debug_image = draw_info(debug_image, fps)
                    return debug_image
        else:
            debug_image = draw_info(debug_image, fps)
            return debug_image

    def speak(self, classification):
        pyttsx3.speak(classification)

    def create_speech_thread(self, classification):
        if self.speech:
            self.timer = self.speech_history.set_speech_timer()
            t1 = Thread(target=self.speak, args=(classification,))
            t1.start()


import cv2
import mediapipe as mp
import numpy as np


class PoseEstimator:
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose

    def __init__(self,
                 min_detection_confidence=0.5,
                 model_complexity=1,
                 min_tracking_confidence=0.5):
        self.pose = mp.solutions.pose.Pose(min_detection_confidence=min_detection_confidence,
                                           model_complexity=model_complexity,
                                           min_tracking_confidence=min_tracking_confidence)

    def process(self, img):
        return self.pose.process(img)

    @classmethod
    def draw_landmarks(cls, img, results):
        cls.mp_drawing.draw_landmarks(
            img,
            results.pose_landmarks,
            cls.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=cls.mp_drawing_styles.get_default_pose_landmarks_style()
        )

import cv2
import threading


class VideoCamera(object):
    def __init__(self, device=0, width=960, height=540, ):
        self.isRquired = True
        self.device = device
        self.width = width
        self.height = height

    def initilize_cam(self):
        self.video = cv2.VideoCapture(self.device)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def release(self):
        self.grabbed, self.frame = None, None
        self.video.release()

    def get_frame(self):
        image = self.frame
        return image


    def update(self):
        while self.isRquired:
            (self.grabbed, self.frame) = self.video.read()
            return True
        else:
            self.release()
            return False


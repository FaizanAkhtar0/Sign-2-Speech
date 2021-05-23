import time
from threading import Thread

import pyttsx3
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators import gzip

from core.util_models.camera import VideoCamera
from core.deep_models.classifier_loader import ClassifierLoader

from core.models import HistoryModel

cam = VideoCamera()
clf = ClassifierLoader(speech=True)


# Create your views here.

def home(request):
    if request.method == 'GET':
        return render(request, 'index.html', {'form': 'Working!'})
    else:
        return None


def camera(request):
    if request.method == 'GET':
        return render(request, 'camera.html', {'form': 'working!'})
    else:
        return None


def history(request):
    if request.method == 'GET':
        query_set = HistoryModel.objects.all()
        return render(request, 'history.html', {'history': query_set})


def delete_speech(request, id):
    HistoryModel.objects.filter(id=id).delete()
    query_set = HistoryModel.objects.all()
    return render(request, 'history.html', {'history': query_set})


def frame_generator(camera):
    while camera.update():
        frame = camera.get_frame()
        frame = clf.classify(frame)
        if frame is not None:
            frame = clf.web_presentable_frame(frame)
            yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n'
            )
        else:
            raise Exception("Got an Empty Frame, Check Camera!")


@gzip.gzip_page
def live_feed(request):
    try:
        global cam
        cam.isRquired = True
        cam.initilize_cam()
        return StreamingHttpResponse(
            frame_generator(cam), content_type="multipart/x-mixed-replace;boundary=frame"
        )
    except:
        return None


def stop_live_feed(request):
    try:
        global cam
        cam.isRquired = False
        return render(request, 'camera.html', {'form': 'Working!'})
    except:
        pass


def speech(request, id):
    if request.method == 'GET':
        query_set = HistoryModel.objects.all()
        filtered_obj = query_set.get(id=id)
        sentence_list = str(filtered_obj.history).split('.')
        voice = VoiceHelper()
        voice.create_speech_thread(' '.join(sentence_list))
        return render(request, 'history.html', {'history': query_set})


class VoiceHelper:
    def __init__(self, sleep_interval=5):
        self.sleep_interval = sleep_interval
        self.timer = time.time()

    def speak(self, classification):
        pyttsx3.speak(classification)

    def create_speech_thread(self, classification):
        if self.check_timer(self.timer):
            self.timer = self.set_speech_timer()
            t1 = Thread(target=self.speak, args=(classification,))
            t1.start()

    def set_speech_timer(self):
        return time.time() + self.sleep_interval

    def check_timer(self, timer):
        return True if time.time() >= timer else False


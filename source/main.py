import pyfakewebcam
import cv2

FRAME_HEIGHT, FRAME_WIDTH = 720, 1280
INPUT = '/dev/video0'
OUTPUT = '/dev/video20'

camera_input = cv2.VideoCapture(INPUT)
camera_input.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera_input.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
fake_camera = pyfakewebcam.FakeWebcam(OUTPUT, FRAME_WIDTH, FRAME_HEIGHT)
while True:
    try:
        _, frame = camera_input.read()
        print(frame.shape)
        processed_frame = frame[:, :, ::-1]
    except Exception as e:
        print(e)
    fake_camera.schedule_frame(processed_frame)



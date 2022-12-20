# import the necessary packages
from threading import Thread
import sys
import cv2
import time
import torch 
from util_graphics import overlay_scoreboard, is_graphic_ready
import numpy as np

# import the Queue class from Python 3
if sys.version_info >= (3, 0):
	from queue import Queue

# otherwise, import the Queue class for Python 2.7
else:
	from Queue import Queue


class Stream:
	def __init__(self, path, point_started, point_over, set_over, match_over, reset, queue_size=32):
		# initialize the file video stream along with the boolean
		# used to indicate if the thread should be stopped or not
		# self.human_detector = torch.hub.load('./yolov5', 'yolov5n', source='local')
		self.point_started = point_started
		self.point_over = point_over
		self.set_over = set_over
		self.match_over = match_over
		self.reset = reset
		self.human_detector = torch.hub.load('./yolov5', 'custom', path='./weights/Generalisedv5S.pt', source='local')
		if torch.cuda.is_available():
			self.human_detector.to('cuda:0')
		# self.human_detector.conf=0.4
		# self.human_detector.amp=True
		self.path = path
		self.stream = cv2.VideoCapture(path)
		# self.fps = int(self.stream.get(5))
		self.fps=25
		print("fps_check FPS", self.fps)
		self.stopped = False
		self.scoreboard = None
		self.rallyboard = None
		self.speedboard = None
		self.afterGame = None
		self.afterMatch = None

		# initialize the queue used to store frames read from
		# the video file
		self.Q = Queue(maxsize=queue_size)
		self.Q_results = Queue(maxsize=queue_size)
		self.Q_status = Queue(maxsize=queue_size)
		# intialize thread
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True
 
	def start(self):
		# start a thread to read frames from the file video stream
		self.thread.start()
		return self

	def update(self):
		# keep looping infinitely
		k=0
		while True:
			# if the thread indicator variable is set, stop the
			# thread
			if self.stopped:
				break

			# otherwise, ensure the queue has room in it
			if not self.Q.full():
				# read the next frame from the file
				# Uncommment to convert 60fps tp 30fps
				# self.stream.read()
				(grabbed, frame) = self.stream.read()

				# if the `grabbed` boolean is `False`, then we have
				# reached the end of the video file
				if not grabbed:
					self.stopped = True
					
    
				if frame is not None:
					brod_frame = np.zeros((1080,1920,3), np.uint8)
					# brod_frame[:,:,1] = 255
					# brod_frame =overlay_scoreboard(brod_frame, self.scoreboard)
					# if is_graphic_ready(self.rallyboard):
					# 	brod_frame = self.rallyboard.draw_on(brod_frame)
					# 	if self.speedboard is not None and not is_graphic_ready(self.rallyboard):
					# 		self.speedboard.ready = True
					# if is_graphic_ready(self.speedboard):
					# 	brod_frame = self.speedboard.draw_on(brod_frame)

					# if is_graphic_ready(self.afterGame):
					# 	brod_frame = self.afterGame.draw_on(brod_frame)
					if self.point_started.is_set():
						self.Q_status.put('point_started')
					elif self.point_over.is_set():
						if self.set_over.is_set():
							self.Q_status.put('point_over,set_over')
							self.set_over.clear()
						elif self.match_over.is_set():
							self.Q_status.put('point_over,match_over')
							self.match_over.clear()
						else:
							self.Q_status.put('point_over')
						self.point_over.clear()
					elif self.reset.is_set():
						self.Q_status.put('reset')
						self.reset.clear()
					else:
						self.Q_status.put('None')
      
					self.Q.put(frame)
					s = time.time()
					self.Q_results.put(self.human_detector(frame))
					# print(round(1000*(time.time()-s),2))
			else:
				time.sleep(0.1)  # Rest for 10ms, we have a full queue


		self.stream.release()

	def read(self):
		# return next frame in the queue
		return self.Q_results.get(),self.Q.get(), self.Q_status.get()

	# Insufficient to have consumer use while(more()) which does
	# not take into account if the producer has reached end of
	# file stream.
	def running(self):
		return self.more() or not self.stopped

	def more(self):
		# return True if there are still frames in the queue. If stream is not stopped, try to wait a moment
		tries = 0
		while self.Q.qsize() == 0 and not self.stopped and tries<=5:
			time.sleep(0.1)
			tries += 1

		return self.Q.qsize() > 0

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		# wait until stream resources are released (producer thread might be still grabbing frame)
		self.thread.join()

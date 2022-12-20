import json
import threading
import time
import tkinter.font as tkFont
from tkinter import *
from tkinter import messagebox
from urllib.request import urlopen
import argparse
import cv2
import numpy as np

click_count = 0
coordinates = []
image = None
nextPageButton = 'normal'
resolution = ""


def mouse_click(event, x, y, flag, params):
    global click_count
    global coordinates
    global nextPageButton

    if event != 0 and click_count < 8:
        print("Running on click")
        click_count += 1
        print(click_count)
        if click_count in [1, 3, 5, 7] and event == cv2.EVENT_LBUTTONDOWN:
            print(click_count)
            print("Inside the event")
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.circle(image, (int(x), int(y)), 3, (0, 0, 0), -1)
            cv2.putText(image, str(x) + ',' + str(y), (x, y), font, 1, (255, 0, 0), 2)
            coordinates.append([x, y])
            cv2.imshow('Draw Coordinates', image)
        else:
            if event == cv2.EVENT_RBUTTONDOWN:
                print("Right Click, decreasing count")
                click_count -= 4
                coordinates.pop()
                print(coordinates)

    elif event == 1 and click_count > 7:
        print(click_count)
        print(coordinates)
        nextPageButton = 'normal'
        json_co = {"coordinates": coordinates}
        with open('coordinates.json', 'w') as f:
            json.dump(json_co, f)
        with open('../nodecg/bundles/graphics/graphics/coordinates.json', 'w') as f:
            json.dump(json_co, f)
        cv2.destroyAllWindows()
    elif event == 2:
        click_count -= 3
        coordinates.pop()
        print(coordinates)

def draw_coordinates():
    global click_count
    global coordinates
    global image
    global resolution

    coordinates = []
    click_count = 0
    # image = cv2.imread("LOGO.png")
    if image is None:
        messagebox.showwarning("LOADING", "Please wait... We are Still Loading the Image")
    else:
        width = 1000
        height = 1000
        print("Image Size")
        print(image.shape)
        # image = cv2.resize(image, (width, height))
        cv2.putText(image, "LEFT CLICK ON TABLE CORNERS", (int(width * 0.10), int(height * 0.03)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1)
        cv2.putText(image, "RIGHT CLICK TO UNDO", (int((width * 0.10) + (width / 2)),
                                                   int(height * 0.03)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255),
                    1)
        # Get Image to Draw
        cv2.imshow("Draw Coordinates", image)
        cv2.setMouseCallback("Draw Coordinates", mouse_click)
        cv2.waitKey(0)


def get_image(src):
    global image
    global resolution
    # vid_cap = cv2.VideoCapture("../../videos/wtt_trim.mp4")
    # vid_cap = cv2.VideoCapture('rtmp://stream.setka-cup.com/ai/test')
    vid_cap = cv2.VideoCapture(int(src))
    
    # image = cv2.imread('test1.png')
    # resolution = (width, height)
    start_time = time.time()
    loopout = True
    while loopout:
        i, z = vid_cap.read()
        imageaverage = np.average(np.average(np.average(z, axis=0), axis=0), axis=0)
        print(imageaverage)
        if 200 > imageaverage > 60:
            loopout = False
        elif (time.time() - start_time) > 5:
            loopout = False
        cv2.imwrite('demo.png', z)
        break


    image = z
    resolution = (image.shape[1], image.shape[0])
    vid_cap.release()

def main(src):

    image_thread = threading.Thread(target=get_image(src))
    image_thread.start()

    # ToDo Use GoPRO and try to capture frame once and add next page option after this.

    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    print(width)
    print(height)
    print(width * 0.005)
    print(height * 0.005)
    root.geometry("%dx%d" % (width, height))
    fontStyle = tkFont.Font(family="Lucida Grande", size=40)
    bg = PhotoImage(file="graphics/LOGO1.png")

    label1 = Label(root, image=bg)
    label1.place(x=int(width * 0.08), y=int(height * 0.08))

    label2 = Label(root, text="Stupa Scoring and Broadcasting", font=fontStyle, foreground='turquoise')
    label2.pack(pady=50)
    # f = ("Times bold", 14)

    DrawCoordinates = Button(root, text="Get Table Coordinates", command=draw_coordinates, width=int(width * 0.013),
                            height=int(height * 0.004), bg="turquoise", fg="white").place(x=int(width * 0.10),y=int(height * 0.08))

    matchidinput = StringVar()
    textinput = Entry(root, textvariable=matchidinput, width=10)
    textinput.pack(fill='x', expand=True)
    textinput.focus()

    textinput.insert(0, "Enter any Text")

    root.mainloop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    args = parser.parse_args()
    if args.src:
        main(args.src)

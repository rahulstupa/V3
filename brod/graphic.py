import numpy as np
import cv2 
from PIL import Image
import os.path as osp
import glob

def read_graphic(name):
    html = '/' not in name
    if html:
        path = osp.join('./graphics/htmlResults/', name)
    else:
        path = name
    return cv2.imread(path,cv2.IMREAD_UNCHANGED)

class SequenceGraphic:
    def __init__(self, path, ready):
        overlays = glob.glob(osp.join(path,"*.png"))
        overlays.sort()
        self.overlays = [cv2.imread(im, cv2.IMREAD_UNCHANGED) for im in overlays]
        self.ready = ready
    def draw_on(self, bgr):
        if len(self.overlays)>1:
            overlay = self.overlays.pop(0)
            overlay = Image.fromarray(overlay)
            bgr = Image.fromarray(bgr)
            bgr.paste(overlay, (0,0), overlay)
            return np.array(bgr)
            
        else:
            self.ready = False
            return bgr
    
class AnimatedGraphic:
    def __init__(self, name, fps, duration, ready, partial=True, delay=None):
        self.name = name
        self.img = read_graphic(name)
        if self.img.shape[:2]!=(1080,1920):
            self.img = cv2.resize(self.img, (1920,1080))
        self.frame_duration = duration*fps
        appear_alphas = list(range(1,self.frame_duration,3))
        stay_alphas = [self.frame_duration]*(self.frame_duration-2*self.frame_duration//3)
        dissapear_alphas = list(range(self.frame_duration//3,-1,-3))
        alphas = [*appear_alphas,*stay_alphas,*dissapear_alphas]
        if delay is not None:
            delay_alphas = [0]*(delay*fps)
            alphas = [*delay_alphas, *alphas]
        self.alphas = [alpha/self.frame_duration for alpha in alphas]
        self.ready=ready
        self.partial = partial 
        if partial:
            y,x = self.img[:,:,3].nonzero() 
            minx = np.min(x)
            miny = np.min(y)
            maxx = np.max(x)
            maxy = np.max(y)
            self.bounds = [minx,miny,maxx,maxy]
        else:
            rgb = self.img[:,:,:3]
            _, alpha = cv2.threshold(rgb, 0, 255, cv2.THRESH_BINARY)
            self.alpha = cv2.cvtColor(alpha, cv2.COLOR_BGR2GRAY)
            self.cropImg = cv2.bitwise_and(rgb,rgb,mask = self.alpha)
            
          
    def draw_on(self, bgr):
        if len(self.alphas)>1:
            if self.partial:
                minx,miny,maxx,maxy = self.bounds
                cropImg = self.img[miny:maxy, minx:maxx, :3]
                toreplace = bgr[miny:maxy, minx:maxx]
                cropImg, toreplace = Image.fromarray(cropImg), Image.fromarray(toreplace)
                toreplace = Image.blend(toreplace,cropImg,self.alphas.pop(0))
                bgr[miny:maxy, minx:maxx] = toreplace
                return bgr
            else:
                toreplace = cv2.bitwise_and(bgr,bgr,mask =self.alpha)
                remaining = cv2.bitwise_and(bgr,bgr,mask =255-self.alpha)
                cropImg, toreplace = Image.fromarray(self.cropImg), Image.fromarray(toreplace)
                toreplace = Image.blend(toreplace,cropImg,self.alphas.pop(0))
                return remaining+np.array(toreplace)
        else:
            self.ready=False
            return bgr

class CombinedGraphic:
    def __init__(self, graphics, ready):
        self.graphics  = graphics
        self.ready = ready
    def draw_on(self, bgr):
        ready_status = []            
        for graphic in self.graphics:
            ready_status.append(graphic.ready)
            if graphic.ready:
                bgr = graphic.draw_on(bgr)
                
        if all(ready_status)==False:
            self.ready = False
        
        return bgr

class ChainGraphics:
    def __init__(self, graphics, ready):
        self.graphics  = graphics
        self.counter = 0
        self.ready = ready
    
    def draw_on(self, bgr):
        if self.graphics[self.counter].ready:
            return self.graphics[self.counter].draw_on(bgr)
        else:  
            self.counter+=1
            if self.counter==len(self.graphics):
                self.ready = False
            else:
                self.graphics[self.counter].ready=True
                return self.graphics[self.counter].draw_on(bgr)
        return bgr        
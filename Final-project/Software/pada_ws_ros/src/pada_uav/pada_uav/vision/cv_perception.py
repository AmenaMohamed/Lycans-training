import cv2
#------------global constants---------#
#distance constants
TOOFAR= 2
FAR=1
MID =0
NEAR=-1
#command constants
RTL=1
LAND=2
NONE=0
#obstacle_direction 
RIGHT =1
LEFT = -1
CENTER=0
#left = -1 , center = 0 , right = 1
#Refrence : https://rahuldangi.medium.com/connect-pc-to-phone-camera-over-http-protocol-47410ec9e811
#I installed ip webcam app  on my phone , then took the ip address , accessed it here

#stream = cv2.VideoCapture('http://192.168.1.8:8080/video')

#about findcontours :https://docs.opencv.org/3.4.20/d4/d73/tutorial_py_contours_begin.html
#about obstacle_direction(how to get contour center): https://www.geeksforgeeks.org/python/python-opencv-find-center-of-contour/

ip_address="192.168.1.5"
port="8081"
username="admin"
password="admin"

class cameraStream():
    def __init__(self):

        self.stream=cv2.VideoCapture(f'http://{username}:{password}@{ip_address}:{port}/video')
        self.stopped=False
    # Use the next line if your camera has a username and password
    # stream=cv2.VideoCapture('protocol://username:password@IP:port/1')
    def get_frame(self):
        if not self.stream.isOpened():
            return None
        else:
            _ , f = self.stream.read()
            return f

    def stop(self):
        self.stopped=True
        self.stream.release()
        #cv2.destroyAllWindows()
    
#----------------------------------TargetDetector Class---------------------------------#

class TargetDetector():
    def __init__(self):
        self.blue_lower =(100, 150, 0)
        self.blue_upper =(140, 255, 255)
        self.green_lower = (35, 40, 40)
        self.green_upper =(85, 255, 255)

        self.cnts=[]

    
    def detect_blue_rectangle(self,frame):
        self.hsvframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.blue_mask = cv2.inRange(self.hsvframe, self.blue_lower, self.blue_upper) 
        
        #get object borders using findcontours
        self.cnts, _ = cv2.findContours(self.blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(self.cnts) != 0: 
            #take first biggest 5 contours
            self.cnts = sorted(self.cnts, key=cv2.contourArea, reverse=True)[:5]
            for i in self.cnts:
                if cv2.contourArea(i)>500 :
                    # Approximate and draw contour
                    epsilon=0.02 * cv2.arcLength(i, True)
                    approx = cv2.approxPolyDP(i, epsilon, True)

        # 6. Bounding Visuals: Draw a bounding box around the detected object on the live output feed.
                    cv2.drawContours(frame, [approx], 0, (0, 0, 255), 5)

                    # 3. Classify shape based on number of vertices
                    num_vertices = len(approx)
                    if num_vertices == 4:
                        return RTL # RTL(blue rectangle) = 1

            return NONE
        else:
            # if findcontours return nothing -> return 0
            return NONE


    def detect_green_circle(self,frame):
        self.hsvframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.green_mask = cv2.inRange(self.hsvframe, self.green_lower, self.green_upper) 
        
        #get object borders using findcontours
        self.cnts, _ = cv2.findContours(self.green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(self.cnts) != 0: 
            #take first biggest 5 contours
            self.cnts = sorted(self.cnts, key=cv2.contourArea, reverse=True)[:5]
            for i in self.cnts:
                if cv2.contourArea(i)>500 :
                    # Approximate and draw contour
                    epsilon=0.02 * cv2.arcLength(i, True)
                    approx = cv2.approxPolyDP(i, epsilon, True)

        # 6. Bounding Visuals: Draw a bounding box around the detected object on the live output feed.
                    cv2.drawContours(frame, [approx], 0, (0, 0, 255), 5)

                    # 3. Classify shape based on number of vertices
                    num_vertices = len(approx)
                    if num_vertices >8 :

                        #cv2.drawContours(frame, self.cnts, -1, (0, 255, 0), 2)
                        return LAND # LAND(green circle) = 2
            return NONE
        else:
            # if findcontours return nothing -> return 0
            return NONE
            

#---------------------------------ObstacleDetector Class--------------------------------#

class ObstacleDetector():

    def __init__(self):
        

# ColorThresholding: Segment the frame to isolate Red and Green regions using cv2.inRange().
        self.red_lower1 =(0, 120, 70)
        self.red_upper1= (10, 255, 255)
        
        self.red_lower2 = (170, 100, 70)
        self.red_upper2 = (180, 255, 255)
        #creating a mask
        self.cnts=[]
        
    def detect_red_obj(self,frame):
        #applying a filter
        self.hsvframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.red_mask = cv2.inRange(self.hsvframe, self.red_lower1, self.red_upper1) | cv2.inRange(self.hsvframe, self.red_lower2, self.red_upper2)
        red_filter = cv2.bitwise_and(self.hsvframe, self.hsvframe,mask=self.red_mask)

        #get object borders using findcontours
        self.cnts, _ = cv2.findContours(self.red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(self.cnts) == 0: 
            # if findcontours return nothing -> return False
            return False
        else:
            # else : draw red line around the object , return -> True
            cv2.drawContours(frame, self.cnts, -1, (0, 255, 0), 2)
            return True


    def obstacle_distance(self,frame):
        #using the found object before to calculate area of using cv2.contourArea
        largest_contour = max(self.cnts, key=cv2.contourArea)
        obstacle_area = cv2.contourArea(largest_contour)
        #calculating frame area
        height, width, _ = frame.shape 
        total_frame_area = height * width
        #cal
        self.ratio = (obstacle_area / total_frame_area)
        #find ratio of object area to frame area
        #too far=(<5%) 2, far= 1(5-10%) , mid(10-15%)=0, near=-1 (>=15%)
        if self.ratio<0.05:
            return TOOFAR # Too far / Ignore
            
        elif 0.05< self.ratio < 0.10:
            return FAR # 5-10% = Far
    
        elif 0.10 <= self.ratio < 0.15:
            return MID # 10-15% = Mid
        else:
            return NEAR # >= 15% = Near / Danger


    def obstacle_direction(self,frame):
        largest_contour = max(self.cnts, key=cv2.contourArea)
        _,width, _ = frame.shape
        frame_div=width/3
        
        M = cv2.moments(largest_contour)
        cx = int(width / 2)

        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])

        if 0< cx <= frame_div:
            return RIGHT
        if frame_div< cx <= 2*frame_div:
            return CENTER
        if 2*frame_div< cx <= 3*frame_div:
            return LEFT

        return CENTER
         #left = -1 , center = 0 , right = 1
    
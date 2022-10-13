import cv2
import numpy as np
import PySimpleGUI as sg

sg.theme('DarkAmber')  

img=np.zeros([512, 512, 3], np.uint8)
for i in range(img.shape[1]):
	d = int(np.ceil(i/2))
	img[:,i,:] = np.array([d,d,d],np.uint8)

img = cv2.applyColorMap(img,cv2.COLORMAP_HSV)
imgbytes = cv2.imencode(".png", img)[1].tobytes()


feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)

# Parameters for Lucas Kanade optical flow
lk_params = dict(winSize=(15, 15),maxLevel=2,criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

ColumnA = [
[sg.Text(' Video Input: ')],
[ sg.Input(enable_events=True, key="VIDEOBROWSE"), sg.FileBrowse('Search Video')],
[sg.Text(' Output Folder:')],
[sg.Input(enable_events=True, key="OUTPUTBROWSE"), sg.FolderBrowse('Search Folder')],

[sg.Text('Tracking Retangle: ', key='up_Text')],
[sg.Text('Pos - X '),sg.Slider(range=(0,180),size=(40, 15), default_value=0, key='rectX', orientation='h',enable_events=True, disable_number_display=True,disabled=True)],
[sg.Text('Pos - Y'),sg.Slider(range=(0,255),size=(40, 15), default_value=0,  key='rectY', orientation='h',enable_events=True, disable_number_display=True,disabled=True)],
[sg.Text('Height ',key= 'txtHeight',size=(8, 1)),sg.Slider(range=(0,255),size=(40, 15), default_value=100,  key='rectHeight', orientation='h',enable_events=True, disable_number_display=True,disabled=True)],
[sg.Text('Width ',key= 'txtWidth',size=(8, 1)),sg.Slider(range=(0,180),size=(40, 15), default_value=100, key='rectWidth', orientation='h',enable_events=True, disable_number_display=True,disabled=True)],
[sg.Button('Get Starting Tracking Points',key='StartPoints',disabled=True)],
[sg.Button('StartTracking',key='StartTracking',disabled=True),sg.Text('...',key='trackingINFO',size=(40, 1))], 
]

ColumnB = [
[sg.Image(data=imgbytes,key="IMAGE",size=(512,512))],
]

layout = [
    [
        sg.Column(ColumnA),
        sg.VSeperator(),
        sg.Column(ColumnB),
    ]
]

# Create the Window and initialize variables
window = sg.Window('SimpleTracking', layout)
first_frame = None
old_gray = None
frame = None
cap = None
out = None
p0 = np.array([])
frameheight = 0
framewidth = 0
ret = False
Start = False
red = [0,0,255]
blue = [255, 0, 0]
diffx = 0
diffy = 0
height = 0
width = 0

def UpdateRectangle(first_frame):
	frame = first_frame.copy()
	cv2.rectangle(frame, [int(values['rectX']),int(values['rectY'])], [int(values['rectX']+values['rectWidth']),int(values['rectY']+values['rectHeight'])], red, 2)
	return frame

def GetStartP0(first_frame):
	old_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
	px = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
	L = []
	for point in px:
	    if (point[0][0] > values['rectX']) and (point[0][0] < values['rectX']+values['rectWidth']):
	        if (point[0][1] > values['rectY']) and (point[0][1] < values['rectY']+values['rectHeight']):
	            L.append(point)
	p0 = np.array(L)
	return p0

def GetDiff(p0):
	sumx = 0
	sumy = 0

	for new in p0:
	    sumx += new[0][0]
	    sumy += new[0][1]

	d = 1
	if len(p0)> 0:
	    d = len(p0)
	meanx = int(sumx/d)
	meany = int(sumy/d)

	diffy = int(values['rectY'] - meany)
	diffx = int(values['rectX'] - meanx)

	return(diffx,diffy)

def disableAll():
	window['StartPoints'].update(disabled=True)
	window['StartTracking'].update(disabled=True)
	window['rectX'].update(disabled=True)
	window['rectY'].update(disabled=True)
	window['rectHeight'].update(disabled=True)
	window['rectWidth'].update(disabled=True)

def enableSlidersAndStart():
	window['StartPoints'].update(disabled=False)
	window['rectX'].update(disabled=False)
	window['rectY'].update(disabled=False)
	window['rectHeight'].update(disabled=False)
	window['rectWidth'].update(disabled=False)

while True:
	event, values = window.read(timeout=20)
	if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
		break

	if event == "VIDEOBROWSE":
		enableSlidersAndStart()
		cap = cv2.VideoCapture(values['VIDEOBROWSE'])
		ret, first_frame = cap.read()
		old_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
		frameheight = first_frame.shape[0]
		framewidth = first_frame.shape[1]

		frame = first_frame.copy()
		window["rectX"].update(range=(0,framewidth)  )
		window["rectY"].update(range=(0,frameheight) )
		window["rectHeight"].update(range=(1,frameheight)  )
		window["rectWidth"].update(range=(1,framewidth) )
		
	if ((event == "StartTracking") and (len(p0) > 0 )):	
		diffx,diffy = GetDiff(p0)
		Start = True
		disableAll()
		out = cv2.VideoWriter(values['OUTPUTBROWSE']+'/Output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (int(values['rectWidth']),int(values['rectHeight'])) )
		

	if values['VIDEOBROWSE'] != '':
		if not Start:
			if ((event == "rectX") and (ret == True)):
				frame = UpdateRectangle(first_frame)
			if ((event == "rectY") and (ret == True)):
				frame = UpdateRectangle(first_frame)	
			if ((event == "rectHeight") and (ret == True)):
				window["txtHeight"].update("Height " + str(int(values['rectHeight'])))
				frame = UpdateRectangle(first_frame)
			if ((event == "rectWidth") and (ret == True)):
				window["txtWidth"].update("Width " + str(int(values['rectWidth'])))	
				frame = UpdateRectangle(first_frame)
			if (((event == "StartPoints") and (ret == True)) or ((event == "OUTPUTBROWSE") and (ret == True)) ):	
				p0 = GetStartP0(first_frame)
				if len(p0) > 0 and values['OUTPUTBROWSE'] != '':
					window['StartTracking'].update(disabled=False)
				else:
					window['StartTracking'].update(disabled=True)

			for p in p0:
				cv2.circle(frame, (int(p[0][0]), int(p[0][1])), 5, blue, -1)
			
			scale = 512/frameheight
			width = int(framewidth * scale)

			Resized = cv2.resize(frame,(width,512))
			imgbytes = cv2.imencode(".png", Resized)[1].tobytes()
			window["IMAGE"].update(data=imgbytes)
		
		else:

			ret, frame = cap.read()
	
			if ret:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

				good_new = p1[st == 1]
				good_old = p0[st == 1]

				# Draw tracked points
				sumx = 0
				sumy = 0
				cleanFrame = frame.copy()
				for new in good_new:
					frame = cv2.circle(frame, (int(new[0]), int(new[1])), 5, blue, -1)
					sumx += new[0]
					sumy += new[1]

				meanx = int(sumx/len(good_new))
				meany = int(sumy/len(good_new))

				t0 = [meanx + diffx,meany + diffy] 
				t1 = [t0[0]+int(values['rectWidth']),t0[1]+int(values['rectHeight'])]

				# Draw the Rectagle
				frame = cv2.rectangle(frame, t0, t1, red, 2)

				# Opens a new window and displays the input
				# frame
				scale = 512/frameheight
				width = int(framewidth * scale)

				Resized = cv2.resize(frame,(width,512))
				imgbytes = cv2.imencode(".png", Resized)[1].tobytes()
				window["IMAGE"].update(data=imgbytes)

				progress = (int(cap.get(cv2.CAP_PROP_POS_FRAMES))/int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) )*100

				window["trackingINFO"].update(" - Tracking - "+ str("{:.2f}".format(progress)) + " %")
				crop = cleanFrame[t0[1]:t1[1], t0[0]:t1[0]]
				out.write(crop)

				old_gray = frame_gray.copy()
				p0 = good_new.reshape(-1, 1, 2)

			if not ret:
				print("Last Frame")
				Start = False
				out.release()
				cap = cv2.VideoCapture(values['VIDEOBROWSE'])
				ret, first_frame = cap.read()
				enableSlidersAndStart()
				old_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
				frame = first_frame.copy()
				frame = UpdateRectangle(first_frame)
				p0 = []

window.close()
cap.release()
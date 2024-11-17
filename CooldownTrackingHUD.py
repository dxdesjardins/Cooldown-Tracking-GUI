import threading, time
import win32api, win32con, win32gui, math
import cv2, numpy as np
import win32ui

# Script that searches for images at specified screen locations and creates progressbars once the images are found.
# Configurable to various factors such as: color, size, frequency of trigger, refresh rate, image tolerance.
# Uses the windows API to draw the progress bar to the screen.
# Designed to have minimumal dependance on high level external libraries.
#
# Dependencies: PyWin32, NumPy, OpenCV

# Static Variables
cwd = "sdIm\\"
wR = [0, 0, 1, 1]
p0ImageRect = (88, 116, 246, 149)
p1ImageRect = (350, 116, 508, 149)
FImageRect = (955, 804, 1005, 851)
CImageRect = (1028, 804, 1084, 851)
hWndGUI = None
pBars = []
colorBlue = 0x00FF0000 # blue
colorRed = 0x000000FF # red
colorGreen = 0x00228B22 # green
colorGrey = 0x00999999 # grey
colorWhite = 0x00FFFFF0 # white
colorBlack = 0x00000000 # black
colorLightBlue = 0x00FFA500 # light blue
colorPurple = 0x00FF00FF # purple

# Settings
imageSearchTimer = 0.03
guiRefreshTime = .2
imageTolerance = 0.996

# Progressbar Positions
pb1WHBXY = (45, 3, 1, 980, 290)
pb2WHBXY = (45, 3, 1, 980, 281)
pb3WHBXY = (45, 3, 1, 980, 272)
pb10WHBXY = (32, 3, 1, 1028, 302)
pb20WHBXY = (32, 3, 1, 1028, 291)
pb30WHBXY = (32, 3, 1, 1028, 280)
pb1Duration = 0
pb1Cooldown = 25.5
pb1ImageRECT = p0ImageRect

class ProgressBar:
	def __init__(self, wHBXY, duration, cooldown, imageRECT, imageNames, activeColor, cdColor, bgActiveColor, bgCDColor, earlyResetTime):
		global pBars
		self.wHBXY = wHBXY
		self.duration = duration
		self.cooldown = cooldown
		self.iSR = imageRECT
		self.imageNames = imageNames
		self.activeColor = activeColor
		self.cdColor = cdColor
		self.bgActiveColor = bgActiveColor
		self.bgCDColor = bgCDColor
		self.durationPercent = 0
		self.cooldownPercent = 0
		self.progressThreadID = 0
		self.timeElapsed = 0
		self.earlyResetTime = earlyResetTime
		pBars.append(self)

class WindowCapture:
	#Properties
	hwnd = None
	def __init__(self, window_name=None):
		if window_name is None:
			self.hwnd = win32gui.GetDesktopWindow()
		else:
		#Call specific window to capture
			self.hwnd = win32gui.FindWindow(None, window_name)
			if not self.hwnd:
				raise Exception("Window not found: {}".format(window_name))
	def ScrShot(self, x1, y1, x2, y2):
		bmpfilenamename = "out.bmp" #set this
		wDC = win32gui.GetWindowDC(self.hwnd)
		dcObj = win32ui.CreateDCFromHandle(wDC)
		cDC = dcObj.CreateCompatibleDC()
		dataBitMap = win32ui.CreateBitmap()
		dataBitMap.CreateCompatibleBitmap(dcObj, x2 - x1, y2 - y1)
		cDC.SelectObject(dataBitMap)
		cDC.BitBlt((0,0),(x2 - x1, y2 - y1) , dcObj, (x1, y1), win32con.SRCCOPY)
		signedIntsArray = dataBitMap.GetBitmapBits(True)
		img = np.fromstring(signedIntsArray, dtype = "uint8")
		img.shape = (y2 - y1,x2 - x1,4)
		# Save screenshot (debugging)
		#dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
		# Free Resources
		dcObj.DeleteDC()
		cDC.DeleteDC()
		win32gui.ReleaseDC(self.hwnd, wDC)
		win32gui.DeleteObject(dataBitMap.GetHandle())
		img = img[...,:3]
		img = np.ascontiguousarray(img)
		return img

def ImSearch(image, x1, y1, x2, y2, precision=0.8, im=None):
	if im is None:
		im = windowCapture.ScrShot(x1, y1, x2, y2)
	img_rgb = np.array(im)
	img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
	template = cv2.imread(image, 0)
	if template is None:
		raise FileNotFoundError('Image file not found: {}'.format(image))
	res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
	min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
	if max_val < precision:
		return [-1, -1]
	return max_loc

def GetActiveWindow():
	global wR, getWindowRunning
	windowHandle = win32gui.GetForegroundWindow()
	wR = win32gui.GetWindowRect(windowHandle)

def TrackProgress(pBar):
	global guiRefreshTime
	pBar.progressThreadID = threading.current_thread().ident
	startTime = time.time()
	progress = 1
	while progress > 0:
		if pBar.duration == 0:
			break
		progress = 1 - 1 * (time.time() - startTime) / pBar.duration
		if pBar.progressThreadID != threading.current_thread().ident:
			pBar.durationPercent = 0
			print('exited')
			return
		pBar.timeElapsed = time.time() - startTime
		pBar.durationPercent = progress
		if progress <= 0:
			break
		time.sleep(guiRefreshTime)
	pBar.timeElapsed = time.time() - startTime
	startTime = time.time()
	progress = 1
	while progress > 0:
		progress = 1 - 1 * (time.time() - startTime) / (pBar.cooldown - pBar.duration)
		if pBar.progressThreadID != threading.current_thread().ident:
			pBar.cooldownPercent = 0
			return
		pBar.timeElapsed = time.time() - startTime
		pBar.cooldownPercent = progress
		if progress <= 0:
			break
		time.sleep(guiRefreshTime)

def ManageGUI(pBar):
	progressThread = threading.Thread(target=TrackProgress, args=(pBar,))
	progressThread.start()
	UpdateWindow()

def CreateHWND():
	global hWndGUI
	hInstance = win32api.GetModuleHandle()
	className = 'MyWindowClassName'
	wndClass                = win32gui.WNDCLASS()
	wndClass.style          = win32con.CS_HREDRAW | win32con.CS_VREDRAW
	wndClass.lpfnWndProc    = wndProc
	wndClass.hInstance      = hInstance
	wndClass.hCursor        = win32gui.LoadCursor(None, win32con.IDC_ARROW)
	wndClass.hbrBackground  = win32gui.GetStockObject(win32con.WHITE_BRUSH)
	wndClass.lpszClassName  = className
	wndClassAtom = win32gui.RegisterClass(wndClass)
	exStyle = win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT
	style = win32con.WS_DISABLED | win32con.WS_POPUP | win32con.WS_VISIBLE
	hWindow = win32gui.CreateWindowEx(
		exStyle,
		wndClassAtom,
		None, # WindowName
		style,
		0, # x
		0, # y
		win32api.GetSystemMetrics(win32con.SM_CXSCREEN), # width
		win32api.GetSystemMetrics(win32con.SM_CYSCREEN), # height
		None, # hWndParent
		None, # hMenu
		hInstance,
		None # lpParam
	)
	hWndGUI = hWindow
	win32gui.SetLayeredWindowAttributes(hWindow, 0x00ffffff, 255, win32con.LWA_COLORKEY | win32con.LWA_ALPHA)
	win32gui.SetWindowPos(hWindow, win32con.HWND_TOPMOST, 0, 0, 0, 0,
		win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

def wndProc(hWnd, message, wParam, lParam):
	global wR
	if message == win32con.WM_PAINT:
		hdc, paintStruct = win32gui.BeginPaint(hWnd)
		for pBar in pBars:
			if pBar.cooldownPercent > 0:
				# Draw Progressbar Border
				outerRightBound = wR[0] + pBar.wHBXY[3] + pBar.wHBXY[0]
				outerBox = (wR[0] + pBar.wHBXY[3] - pBar.wHBXY[2], wR[1] + pBar.wHBXY[4] - pBar.wHBXY[2], outerRightBound + pBar.wHBXY[2], wR[1] + pBar.wHBXY[4] + pBar.wHBXY[1] + pBar.wHBXY[2])
				bgRgn = win32gui.CreateRectRgnIndirect(outerBox);
				hBrush = win32gui.CreateSolidBrush(pBar.bgCDColor);
				win32gui.FillRgn(hdc, bgRgn, hBrush);
				# Draw Progressbar Fill
				rightBound = wR[0] + pBar.wHBXY[3] + math.trunc(pBar.wHBXY[0] * pBar.cooldownPercent)
				boxTuple = (wR[0] + pBar.wHBXY[3], wR[1] + pBar.wHBXY[4], rightBound, wR[1] + pBar.wHBXY[4] + pBar.wHBXY[1])
				bgRgn = win32gui.CreateRectRgnIndirect(boxTuple);
				hBrush = win32gui.CreateSolidBrush(pBar.cdColor)
				win32gui.FillRgn(hdc, bgRgn, hBrush);
			if pBar.durationPercent > 0:
				# Draw Progressbar Border
				outerRightBound = wR[0] + pBar.wHBXY[3] + pBar.wHBXY[0]
				outerBox = (wR[0] + pBar.wHBXY[3] - pBar.wHBXY[2], wR[1] + pBar.wHBXY[4] - pBar.wHBXY[2], outerRightBound + pBar.wHBXY[2], wR[1] + pBar.wHBXY[4] + pBar.wHBXY[1] + pBar.wHBXY[2])
				bgRgn = win32gui.CreateRectRgnIndirect(outerBox);
				hBrush = win32gui.CreateSolidBrush(pBar.bgActiveColor);
				win32gui.FillRgn(hdc, bgRgn, hBrush);
				# Draw Progressbar Fill
				rightBound = wR[0] + pBar.wHBXY[3] + math.trunc(pBar.wHBXY[0] * pBar.durationPercent)
				boxTuple = (wR[0] + pBar.wHBXY[3], wR[1] + pBar.wHBXY[4], rightBound, wR[1] + pBar.wHBXY[4] + pBar.wHBXY[1])
				bgRgn = win32gui.CreateRectRgnIndirect(boxTuple);
				hBrush = win32gui.CreateSolidBrush(pBar.activeColor)
				win32gui.FillRgn(hdc, bgRgn, hBrush);
		win32gui.EndPaint(hWnd, paintStruct)
		return 0
	elif message == win32con.WM_DESTROY:
		print('Closing the window.')
		win32gui.PostQuitMessage(0)
		return 0
	else:
		return win32gui.DefWindowProc(hWnd, message, wParam, lParam)

def UpdateWindow():
	global hWndGUI
	win32gui.RedrawWindow(hWndGUI, None, None, win32con.WM_PAINT); # Could try win32con.UPDATE_NOW

def ImSearchThread():
	global imageSearchTimer, pBars, imageTolerance
	while True:
		time.sleep(imageSearchTimer)
		for pBar in pBars:
			for imageName in pBar.imageNames:
				pos = ImSearch(imageName, wR[0] + pBar.iSR[0], wR[1] + pBar.iSR[1], wR[0] + pBar.iSR[2], wR[1] + pBar.iSR[3], precision=imageTolerance)
				if pos[0] != -1:
					if (pBar.cooldownPercent <= 0 and pBar.durationPercent <= 0) or (pBar.cooldown - pBar.timeElapsed <= pBar.earlyResetTime):
						print(pBar.timeElapsed)
						#print("Image " + imageName + " found")
						ManageGUI(pBar)

def UpdateGUIThread():
	global guiRefreshTime
	while True:
		time.sleep(guiRefreshTime)
		UpdateWindow()

def InputThread():
	global mousePos
	while True:
		time.sleep(0.005)
		if aKey.Pressed():
			GetActiveWindow()

class PressedKey:
	def __init__(self, buttonInit):
		self.button = buttonInit
		self.buttonHeld = False
	def Pressed(self):
		state = win32api.GetAsyncKeyState(self.button)
		if state != 0 and not self.buttonHeld:
			#print("Pressed:", self.button)
			self.buttonHeld = True
			return True
		elif not state != 0 and self.buttonHeld:
			self.buttonHeld = False
			#print("Unpressed:", self.button)
			return False
		else:
			return False

class PressedMouseButton:
	def __init__(self, buttonInit):
		self.button = buttonInit
		self.buttonHeld = False
	def Pressed(self):
		state = win32api.GetAsyncKeyState(self.button)
		if state != 0 and not self.buttonHeld:
			#print("Pressed:", self.button, "at position", win32api.GetCursorPos())
			self.buttonHeld = True
			return True
		elif not state != 0 and self.buttonHeld:
			self.buttonHeld = False
			#print("Unpressed:", self.button)
			return False
		else:
			return False

if __name__ == "__main__":
	aKey = PressedKey(0x41)
	leftButton = PressedMouseButton(0x01)
	windowCapture = WindowCapture(None)
	GetActiveWindow()

	# Configure Image Search Requirements and Progressbar Settings
	cd = 0.15
	cPB = ProgressBar(pb10WHBXY, 15, 30 * (1 - cd), CImageRect, [cwd + "RyHd30.png", cwd + "RyHd20.png"], colorWhite, colorBlack, colorLightBlue, colorLightBlue, 15)
	capMPB = ProgressBar(pb20WHBXY, 8, 80, p0ImageRect, [cwd + "plaC1.png", cwd + "plaC2.png"], colorWhite, colorBlack, colorBlack, colorWhite, 20)
	FPB = ProgressBar(pb30WHBXY, 8, 40 * (1 - cd), FImageRect, [cwd + "SchRob40.png", cwd + "SchRob30.png", cwd + "SchRob20.png"], colorWhite, colorBlack, colorRed, colorRed, 19)

	# Start Threads
	imSearchThread = threading.Thread(target=ImSearchThread)
	imSearchThread.start()
	updateGUIThread = threading.Thread(target=UpdateGUIThread)
	updateGUIThread.start()
	inputThread = threading.Thread(target=InputThread)
	inputThread.start()
	print("Started")
	CreateHWND()
	win32gui.PumpMessages()

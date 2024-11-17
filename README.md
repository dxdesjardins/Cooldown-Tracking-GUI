# Cooldown Tracking HUD

Searches the active window for images and draws configurable progressbars once they appear. Uses the windows API to draw the progress bar to the screen. Designed to have minimal dependance on high level external libraries.

## Configuration Options

1. Progressbar Location, Color, Size, Refresh Rate, 
2. Search Frequency
3. Image Tolerance

## Dependancies

1. PyWin32
2. NumPy
3. OpenCV

## Usage Example

``` Python
myProgressBar = ProgressBar(
    (45, 3, 1, 980, 290), # The progress bar will have the following characterisics | width: 45, height: 3, border: 1, XLocaction: 980, YLocation: 290
    15, # If the image is found, ProgressBar1 (indicating a status effect timer) will be created and tick down for 15 seconds.
    30, # After ProgressBar1 is depleted, Progressbar2 (indicating a cooldown timer) will tick down for the remaining time (15 seconds remaining)
    (1028, 804, 1084, 851), # Will search in the area defined by a rectangle between pixel location (1028, 804) and (1084, 851)
    ["Image1.png", "Image2.png"], # The tool will search for both Image1.png and Image2.png
    colorWhite, # ProgressBar1 foreground color (indicating a status effect timer)
    colorBlack, # ProgressBar2 foreground color (indicating a cooldown timer)
    colorLightBlue, # ProgressBar1 background color (indicating a status effect timer)
    colorLightBlue, # ProgressBar2 background color (indicating a cooldown timer)
    15)
```
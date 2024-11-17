# Cooldown Tracking HUD

Searches the active window for images and draws configurable progressbars once they appear. Created Progress Bar can have two stages; one to indicate a status effect timer and a second to indicate a subsequent cooldown timer.

Uses the windows API to draw the progress bar to the screen. Designed to have minimal dependance on high level external libraries. 

## Configuration Options

1. Progress Bar Location, Color, Size, Refresh Rate
2. Can search for multiple images simultaneously
3. Search Frequency
4. Image Tolerance

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
    0x00FFFFF0, # ProgressBar1 foreground color (white) (indicating a status effect timer)
    0x00000000, # ProgressBar2 foreground color (black) (indicating a cooldown timer)
    0x00FFA500, # ProgressBar1 background color (light blue) (indicating a status effect timer)
    0x00FFA500, # ProgressBar2 background color (light blue) (indicating a cooldown timer)
    15)
```

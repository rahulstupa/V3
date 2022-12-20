This Document demonstrates how one can setup the code for live demo.

# Stupa Broadcasting

Steps to replicate broadcasting setup:

1. Open a terminal and run: sudo modprobe v4l2loopback
2. Enter password “stupa” when prompted.
3. Open OBS Studio window [1]
4. In Dummy Scene, add video source: Video Capture from ElgatoLink or DroidCam or Media Source for local.
5. Make sure camera input as well as OBS output is set to 50 fps.
6. Start Virtual Cam
7. Open OBS Studio window [2]
8. In Main Scene, add Video Capture from the dummy video feed from virtual cam (from OBS window [1])
9. In terminal: v4l2-ctl --list-devices
10. Note ID of device which is listed under VirtualCam/DummyCam. For example: /dev/video1. Here, remember source ID as 1. (Could be 0/1/2/3/4/ etc.)
11. Open VS Code (Open folder Desktop/latest, should be open by default)
12. In script “app.py” in brod/, change match_ID in line no. 26.
13. Open a terminal window in VS code (Ctrl + ~)
14. In terminal: 
    - `conda activate brod`
    - `cd brod/`
    - `python app.py –src {source ID you looked up in step [6]} –setup`
    -  Example:  `python app.py --src 1 --setup`
    
15. Select the table coordinates in the opened window.
16. Do this only on the first run. The “--setup” option is only required when setting up for the first time, or if table position has been changed. In all other subsequent runs, just run:  python app.py --src 1
17. Open another terminal window in VS code
18. In terminal:
    - `node server.js`
19. Open another terminal window in VS code
20. In terminal:
    - `cd nodecg/`
    - `nodecg start`
21. Open nodecg in a browser localhost
22. Update match ID
23. Go to graphics tab
24. For each element (Pitches, Game Summary, Match Summary, Shot speed, Rally Count, and Scoreboard), do the following:
    - (a) In OBS window [2], add browser source.
    - (b) In URL, copy the URL for the respective element to be displayed,
    - (c) Width = 1920, Height = 1080
25. Come back to the dashboard tab in nodecg tool.
26. Click on “Score trigger button” to make the scoreboard graphic appear
27. Click on “Game summary trigger” and “Match Summary Trigger” to check if the graphics are being properly displayed.
28. Start scoring on the scoring app.


Checks

1. Make sure to check configured output FPS while starting Virtual OBS Feed. ( 25 FPS or 50 FPS).
2. Make sure match ID is same in code and in scoring app.





      
     

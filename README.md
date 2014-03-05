minimal-read-visualization
==========================

A minimal working example for an eyetracking visualization program.
It requires Python 2.7 with the following modules installed:
  - NumPy (v. 1.6.1)
  - SciPy (v. 0.9.0)
  - Scikit-learn (v. 14.0)
  - Pylab
  - PIL (for linux: python-imaging AND python-imaging-tk)
  - TKinter

##Usage

"visualizeData.py" is the main code.
If you run it, a program starts that loads the Stimuli Slides and the appropriate eyetracking data that was recorded.
You can then select an article (each article is made out of several slides) and play or single-step through the gaze track of a particular person (defined in "config.py").

Some features are not fully implemented (can't select a fixation point by its id, "save Image" button just saves a "tmp.ps" file in the working directory). But you can edit the gaze points horizontally by dragging a rectangle around them with the left mouse button and move the highlighted ones with the right mouse button. If "edit mode" is checked the new gaze points will be stored.

####Keyboard bindings:

* Next slide -- "Right" or "d"
* Previous slide -- "Left" or "a"
* Next article -- "Down" or "s"
* Previous article -- "Up" or "w"
* Show complete path -- "Space"


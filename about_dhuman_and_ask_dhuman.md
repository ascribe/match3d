# About dhuman and ask_dhuman

For any pair (i,j) of objects or images, we can ask a human to compare them and say if they're very similar ('V'), similar ('S'), or different ('D'). It's like a distance function: d_human(i,j). It can be used to evaluate the search engine results from a search engine (for a set where dhuman(i,j) is known): an ideal search engine would return very similar items first, followed by similar ones, followed by different ones.

The images shown to the humans should give a good overview of the object, with views from many different directions. That's why I wrote generate_images_for_humans.py. The documentation for that is in the README.md file.

d_human(i,j) can be thought of as a symmetric matrix of tokens because d_human(i,j) = d_human(j,i). That means we only have to store less than half of it.

dhuman.py implements a class DHuman. If you have a set of images in a directory, then you could create an object of class DHuman to store and retrieve the d_human(i,j) of those images. That information gets stored in a "shelf", which is a built-in Python persistent dictionary. The dictionary gets saved to files in the same directory as the images. The dictionary keys are strings of the form "image-6273.png,image-128.jpg" (i.e. two image file basenames, separated by a comma).

If d_human(i,j) isn't known yet, the value is '?', but that token doesn't actually get stored. It's just what the interface returns.

You can use dhuman.py directly, in Python or IPython interactive mode.

I wrote it in a Python 2.7 conda environment, with the Anaconda packages installed. dhuman.py uses the PIL module, which comes with Anaconda, in the pillow package.

Below is an example interactive session. Note that the image gets shown in a separate window, using whatever PIL's Image.show() function calls. In my case, it's imagemagick.

```
(anapy27)troy@hp-ubuntu:~/repos/3d-match$ ipython
Python 2.7.10 |Anaconda 2.2.0 (64-bit)| (default, May 28 2015, 17:02:03) 
Type "copyright", "credits" or "license" for more information.

IPython 3.2.0 -- An enhanced Interactive Python.
Anaconda is brought to you by Continuum Analytics.
Please check out: http://continuum.io/thanks and https://anaconda.org
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object', use 'object??' for extra details.

In [1]: from dhuman import DHuman

In [2]: dh = DHuman('./testset1-images')
3 pairs left to compare.

In [3]: dh.compare_then_save()
Showing sn-10045678.png and sn-10045681.png
Are those very similar (V), similar (S), or different (D)? D
Saved the value 'D' at the key 'sn-10045678.png,sn-10045681.png'

In [4]: dh.get_value_at('sn-10045678.png', 'sn-10045681.png')
Out[4]: 'D'

In [5]: dh.get_value_at('sn-10045678.png', 'sn-10045689.png')
Out[5]: '?'

In [6]: dh.close()

In [7]: quit()
```

If you use dhuman in interactive mode, don't forget to close when you're done. That makes sure the dictionary is all stored to disk. It stores the dictionary in the images directory, in files named 'dhuman_db.bak', 'dhuman_db.dat', and 'dhuman_db.dir'.

Using interactive mode to compare images and store new values in d_human(i,j) isn't great, because when the images get displayed, the python interactive session loses focus.

ask_dhuman.py is a simple GUI frontend that keeps the focus in the GUI at all times. You can use it to rapidly compare images (and save the comparison). Here's an example call to ask_dhuman.py:

```
$ python ask_dhuman.py -i ./testset1-images/
```

To end a session with the ask_dhuman.py GUI, just close the GUI window. It will close the shelf.

If there are no more images to compare, then the GUI will close on its own.

ask_dhuman.py also writes some information to the terminal session where you launched it, for debugging purposes.

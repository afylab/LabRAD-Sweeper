import numpy
from numpy import array
import pyqtgraph as pg

maps = {
    'test':pg.ColorMap(array([0.0,0.5,1.0]),array([[0,0,0],[255,127,0],[255,255,255]])),
    'flag':pg.ColorMap(
        array([n/63.0 for n in range(64)]),
        array([[255*(n%4 in [2,3]),255*(n%4 == 2),255*(n%4 in [1,2])] for n in range(64)])
        ),
    'rb':pg.ColorMap(array([0.0,0.5,1.0]),array([[0,0,255],[255,255,255],[255,0,0]])),
    'bnw':pg.ColorMap(array([0.0,1.0]),array([[0,0,0],[255,255,255]])),
    }
    

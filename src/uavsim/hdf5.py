import faulthandler
import sys

import numpy as np
import h5py
import pyqtgraph as pg
from qtpy import QtGui

faulthandler.enable()


class HDF5Plot(pg.PlotCurveItem):
    def __init__(self, *args, **kwds):
        self.hdf5 = None
        self.limit = 10000  # maximum number of samples to be plotted
        pg.PlotCurveItem.__init__(self, *args, **kwds)

    def set_hdf5(self, data):
        self.hdf5 = data
        self.update_hdf5_plot()

    def append_hdf5(self, data):
        self.hdf5 = np.append(self.hdf5, data) if self.hdf5 is not None else data
        self.update_hdf5_plot()

    def viewRangeChanged(self):
        self.update_hdf5_plot()

    def update_hdf5_plot(self):
        if self.hdf5 is None:
            self.setData([])
            return

        vb = self.getViewBox()

        if vb is None:
            return  # no ViewBox yet

        # Determine what data range must be read from HDF5
        xrange = vb.viewRange()[0]
        start = max(0, int(xrange[0]) - 1)
        stop = min(len(self.hdf5), int(xrange[1] + 2))

        # Decide by how much we should downsample
        ds = int((stop - start) / self.limit) + 1

        if ds == 1:
            # Small enough to display with no intervention.
            visible = self.hdf5[start:stop]
            scale = 1
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.        
            samples = 1 + ((stop - start) // ds)
            visible = np.zeros(samples * 2, dtype=self.hdf5.dtype)
            sourcePtr = start
            targetPtr = 0

            # read data in chunks of ~1M samples
            chunkSize = (1000000 // ds) * ds

            while sourcePtr < stop - 1:
                chunk = self.hdf5[sourcePtr:min(stop, sourcePtr + chunkSize)]
                sourcePtr += len(chunk)

                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk) // ds) * ds].reshape(len(chunk) // ds, ds)

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr + chunk.shape[0] * 2:2] = chunkMin
                visible[1 + targetPtr:1 + targetPtr + chunk.shape[0] * 2:2] = chunkMax
                targetPtr += chunk.shape[0] * 2

            visible = visible[:targetPtr]
            scale = ds * 0.5

        self.setData(visible)  # update the plot
        self.setPos(start, 0)  # shift to match starting index
        self.resetTransform()
        self.scale(scale, 1)  # scale to match downsampling


f = None
curve = None


def update():
    global f

    current_len = len(curve.hdf5) if curve.hdf5 is not None else 0
    f['telemetry']['block0_values'].refresh()
    curve.append_hdf5(f['telemetry']['block0_values'][current_len:, 1])


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    if len(sys.argv) > 1:
        pg.mkQApp()

        plt = pg.plot()
        plt.setWindowTitle('pyqtgraph example: HDF5 big data')
        plt.enableAutoRange(True, True)
        plt.setXRange(5500, 8000)

        fileName = sys.argv[1]

        f = h5py.File(fileName, 'r', swmr=True)
        curve = HDF5Plot()
        plt.addItem(curve)

        timer = pg.QtCore.QTimer()
        timer.timeout.connect(update)
        timer.start(50)

        if (sys.flags.interactive != 1) or not hasattr(pg.QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

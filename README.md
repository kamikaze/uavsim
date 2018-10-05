# UAVSim
UAV simulator that sends NMEA sentences to external devices (i.e. real uav)
It is written in [Python](https://www.python.org/) language and uses [Autobahn](https://autobahn.readthedocs.io/en/latest/) with [AsyncIO](https://docs.python.org/3/library/asyncio.html).
GUI applications are using [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) / [PySide2](http://wiki.qt.io/Qt_for_Python).
Multiple components are being tied together with [CrossbarIO](https://crossbar.io/).

## Setting up an environment ##
`python3.7 -m venv ~/.venv37`

`source ~/.venv37/bin/activate`

## Installing dependencies ##
`python3.7 -m pip install --upgrade -r requirements.txt`

`python3.7 -m pip install --upgrade -r requirements_dev.txt`

## Building ##
`python3.7 setup.py build`

## Installing ##
`python3.7 -m pip install --upgrade dist/uavsim-*.whl`

## Running ##
`
python3.7 -m uavsim
`

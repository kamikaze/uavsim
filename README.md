# UAVSim
UAV simulator that sends NMEA sentences to external devices (i.e. real uav)
It is written in [Python](https://www.python.org/) language and uses [Autobahn](https://autobahn.readthedocs.io/en/latest/) with [AsyncIO](https://docs.python.org/3/library/asyncio.html).
Multiple components are being tied together with [CrossbarIO](https://crossbar.io/).

## Setting up an environment ##
`python3.6 -m venv ~/.venv36`
`source ~/.venv36/bin/activate`

## Installing dependencies ##
`python3.6 -m pip install --upgrade -r requirements.txt`
`python3.6 -m pip install --upgrade -r requirements_dev.txt`

## Building ##
`python3.6 setup.py build`

## Installing ##
`python3.6 -m pip install --upgrade dist/uavsim-*.whl`

## Running ##
`
python3.6 -m uavsim
`

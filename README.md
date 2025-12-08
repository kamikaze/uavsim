# UAVSim
UAV simulator that sends NMEA sentences to external devices (i.e. a real UAV).

The application is a single-process asyncio program with a lightweight in-memory pub/sub bus. The UI is built with PyQt5 and integrated with asyncio via qasync. Components (sim, UAV, stats) run as asyncio tasks and communicate over topics like `sim.telemetry`, `uav.cmd`, `map.position`, and `map.pid`.

## Prerequisites
- Python 3.14.x
- Optional: FlightGear (fgfs) running with telnet on 127.0.0.1:5901

## Setup with uv (recommended)
1. Install uv: https://docs.astral.sh/uv/
2. Sync dependencies:
   - `uv sync`
3. Run the app:
   - `uv run -m uavsim`

## Development
- Source code is under `src/`.
- Tests (if any) are under `tests/` and can be run with `uv run pytest`.

## Notes
- Crossbar/Autobahn have been removed. Older modules (`uavsim.*_adapter`, `uavsim.launcher`) are deprecated stubs kept only for historical reference.

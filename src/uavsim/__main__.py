from uavsim.map import run_map
from uavsim.sim_task import run_sim
from uavsim.uav_task import run_uav
from uavsim.stats_task import run_stats


if __name__ == '__main__':
    # Run a single-process app: Qt UI + asyncio tasks for sim/uav/stats.
    # FlightGear (fgfs) is optional; if not running, the sim task will retry.
    run_map(extra_tasks=[
        lambda: run_sim(telnet_host='127.0.0.1', telnet_port=5901),
        lambda: run_uav(serial_path=None),  # set serial_path to use real serial
        lambda: run_stats(output_dir='/tmp'),
    ])

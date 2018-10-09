import logging
import re
import socket
import telnetlib

logger = logging.getLogger(__name__)


AP_CMD_ENGINE0_THROTTLE = 1
AP_CMD_ENGINE1_THROTTLE = 2

FG_COMMANDS = {
    AP_CMD_ENGINE0_THROTTLE: '/controls/engines/engine[0]/throttle',
    AP_CMD_ENGINE1_THROTTLE: '/controls/engines/engine[1]/throttle'
}
FG_PROP_REGEXP = re.compile(r'([^=]*)\s+=\s*\'([^\']*)\'\s*\(([^\r]*)\)')


class AbstractClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.conn = None
        self.last_cmds = {}

    def connect(self):
        raise NotImplementedError

    def read_telemetry(self):
        pass

    def send_command(self, cmd):
        pass

    def set_property(self, name, value):
        pass

    def set_position(self, lat, lon):
        pass


class TelnetClient(AbstractClient):
    def connect(self):
        if not self.conn:
            self.conn = telnetlib.Telnet(host=self.host, port=self.port)

    def set_property(self, name, value):
        cmd = 'set {} {}\r\n'.format(name, value)
        logger.info(cmd)

        self.conn.write(cmd.encode('ascii'))
        self.conn.read_until(b'/> ')

    def send_command(self, cmd):
        cmd_id, data = cmd.split(',')
        cmd_id = int(cmd_id)

        last_cmd = self.last_cmds.get(cmd_id)
        logger.info('{} {}'.format(cmd_id, last_cmd))

        if last_cmd == data:
            return

        self.set_property(FG_COMMANDS[cmd_id], data)
        self.last_cmds[cmd_id] = data

    def set_position(self, lat, lon):
        self.set_property('position/latitude-deg', lat)
        self.set_property('position/longitude-deg', lon)

    def read_fg_data(self, path):
        self.conn.write('ls {}\r\n'.format(path).encode('ascii'))
        received_data = self.conn.read_until(b'/> ').decode('ascii')
        telemetry = {}

        for row in received_data.split('\r\n')[:-1]:
            match = FG_PROP_REGEXP.match(row)

            if not match:
                continue

            key, value, t = match.groups()

            if not value:
                continue

            if t == 'double':
                # TODO: use Decimal when AutobahnPython will start using cbor2 which supports this
                value = float(value)
            elif t == 'bool':
                value = value == 'true'

            telemetry[key] = value

        return telemetry


class UDPClient(AbstractClient):
    def connect(self):
        if not self.conn:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.conn.bind((self.host, self.port))

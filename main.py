import asyncore
import re
import time
import threading

class GPRSHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        if data:
            pattern = re.compile(r'#(\w*)#(\w*)#(\w*)#(\w*)#(\w*)\r\n#(.*\b)')
            gps_request = pattern.match(data.decode('utf-8'))

            # if the pattern does not match, close the connection
            if gps_request is None:
                print("invalid protocol")
                self.close()
                return

            # get the device id
            device_id = gps_request.group(1)

            # get the GPRS request data
            gps_data = gps_request.group(6).split(',')

            # check if the GPS data coming from the device is valid and not corrupted (A = valid, V = invalid)
            is_valid = gps_data[2]
            if is_valid != "A":
                print(device_id + ": " + is_valid)
                self.close()
                return

            # get latitude and pole: positive, negative
            # South = negative
            # North = positive
            latitude = gps_data[3]
            latitude_pole = -1 if (gps_data[4] == 'S') else 1

            # get longitude and pole: positive, negative
            longitude = gps_data[5]
            # W = negative
            # E = positive
            longitude_pole = -1 if (gps_data[6] == 'W') else 1

            # DDMM.MMMM
            latitude_decimal = (float(latitude[0:2]) + (float(latitude[2:]) / 60.0)) * latitude_pole
            # DDDMM.MMMM
            longitude_decimal = (float(longitude[0:3]) + (float(longitude[3:]) / 60.0)) * longitude_pole

            mysql_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            data_gps = {
                'device_id': device_id,
                'latitude': latitude_decimal,
                'longitude': longitude_decimal,
                'coordinates_updated_at': mysql_datetime,
            }

            print(data_gps)

# ---------------------------------------------------------------------------------
class tlt2hGprsServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        # new connection
        handler = GPRSHandler(sock)

server = tlt2hGprsServer('0.0.0.0', 9999)
asyncore.loop()

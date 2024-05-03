import serial
import pynmea2
import datetime
import time
import pyrebase

config = {
    "apiKey": "AIzaSyCWl5-CwN2NYh_RZm1-P1O0l99Ete2pJe0",
    "authDomain": "eyeblinker-status.firebaseapp.com",
    "databaseURL": "https://eyeblinker-status-default-rtdb.firebaseio.com",
    "storageBucket": "eyeblinker-status.appspot.com",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()


def getLocation():
    gps = ""
    port = "/dev/ttyAMA0"
    ser = serial.Serial(port, baudrate=9600, timeout=0.5)

    for i in range(10):
        ser.readline()
        time.sleep(0.1)

    while True:
        # dataout = pynmea2.NMEAStreamReader()
        # newdata = ser.readline().decode("unicode_escape")
        newdata = ser.readline().decode('ascii', errors='replace').strip()
        print(f"gps: {newdata}")

        if newdata[0:6] == "$GPRMC":
            newmsg = pynmea2.parse(newdata)
            lat = newmsg.latitude
            lng = newmsg.longitude

            latval = "{:.6f}".format(lat)
            longval = "{:.6f}".format(lng)
            gps = f'"{str(latval)},{str(longval)}"'
            date_now, time_now = getDateTime()

            if gps != '"0.000000,0.000000"':
                response = db.child("updates").update(
                    {"date": date_now, "time": time_now, "gps": gps}
                )

                print(response)
                if response:
                    time.sleep(5)
                    return gps


def getDateTime():
    now = datetime.datetime.now()
    date = now.date()
    time = now.time()

    date_str = date.strftime("%Y-%m-%d")
    time_str = time.strftime("%H:%M:%S")
    return date_str, time_str


# while True:
#     getLocation()
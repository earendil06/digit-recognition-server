from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import cv2, imutils, os, uuid, datetime

import numpy as np

app = Flask(__name__)
PORT = 5000


def get_time_italy():
    f = open('/data/italy', 'r')
    timer = f.read()
    f.close()
    date_time_obj = datetime.datetime.strptime(timer, '%Y-%m-%d %H:%M:%S.%f')
    now = datetime.datetime.now()
    return max(0, int(26 - ((now - date_time_obj).total_seconds() / 60)))


def compute_time_france_from_italy(italy_time):
    if 26 >= italy_time >= 15:
        return italy_time - 14
    elif 14 >= italy_time >= 11:
        return 0
    elif italy_time <= 10:
        return 25 - (10 - italy_time)


@app.route("/")
def home():
    return "timer"


@app.route("/italy")
def italy():
    return str(get_time_italy())


@app.route("/france")
def france():
    return str(compute_time_france_from_italy(get_time_italy()))


@app.route("/stats")
def stats():
    results = {}
    fails = {"red": [], "green": []}
    for folder in ["red", "green"]:
        computations = []
        for f in os.listdir(f"/tests/{folder}/"):
            t = get_color(f"/tests/{folder}/{f}")[1]
            computations.append(t)
            if t != folder:
                fails[folder].append(f)
        success = len([c for c in computations if c == folder])
        errors = len([c for c in computations if c != folder])
        results[folder] = {
            'total': len(computations),
            'success': success,
            'errors': errors,
            'ratio': float(success) / len(computations) * 100 if len(computations) > 0 else 'None'
        }
    return render_template('stats.html',
                           results=results, fails=fails)


def download_image_camera(file, url):
    return os.system(
        f'wget --no-check-certificate --no-cache --no-cookies {url} --post-data="action=purge" --output-document={file}')


def save_last_green_date():
    f = open("/data/italy", "w")
    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    f.close()


def compute_time():
    code = download_image_camera("/data/current.jpg", "http://94.125.235.194:8080/record/current.jpg")
    if code == 0:
        color = get_color("/data/current.jpg")[1]
        if color == "green":
            save_last_green_date()


def get_camera_image():
    download_image_camera(f"/tests/{uuid.uuid1()}.jpg", "http://94.125.235.194:8080/record/current.jpg")


def get_color(filename):
    img = cv2.imread(filename)[640:740, 630:660]
    # img = cv2.imread(filename)[640:740, 130:145]
    # img = cv2.add(img, np.array([60.0]))
    b, g, r = cv2.split(img)
    thresh = 127

    im_bw_from_r = cv2.threshold(r, thresh, 255, cv2.THRESH_BINARY)[1]
    im_bw_from_g = cv2.threshold(g, thresh, 255, cv2.THRESH_BINARY)[1]
    im_bw_from_b = cv2.threshold(b, thresh, 255, cv2.THRESH_BINARY)[1]

    percent_up_from_r = cv2.countNonZero(im_bw_from_r[0:50, 0:30])
    percent_up_from_g = cv2.countNonZero(im_bw_from_g[0:50, 0:30])
    percent_up_from_b = cv2.countNonZero(im_bw_from_b[0:50, 0:30])

    percent_down_from_r = cv2.countNonZero(im_bw_from_r[50:100, 0:30])
    percent_down_from_g = cv2.countNonZero(im_bw_from_g[50:100, 0:30])
    percent_down_from_b = cv2.countNonZero(im_bw_from_b[50:100, 0:30])

    up = percent_up_from_r if percent_up_from_r > percent_up_from_g else 0
    down = percent_down_from_g if percent_down_from_g > percent_down_from_r else 0
    #
    # up = max(percent_up_from_r, percent_up_from_g, percent_up_from_b)
    # down = max(percent_down_from_r, percent_down_from_g, percent_down_from_b)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])

    mask = cv2.inRange(hsv, lower_red, upper_red)

    percent = cv2.countNonZero(mask[0:50, 0:30])
    # return [percent, "red" if up > down else "green"]
    #
    # return [(percent_up_from_r, percent_up_from_g, percent_up_from_b, percent_down_from_r, percent_down_from_g,
    #          percent_down_from_b), "red" if up > down else "green"]
    return [percent, "red" if percent != 0 else "green"]


if __name__ == '__main__':
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(func=compute_time, trigger="interval", seconds=15)
    # scheduler.start()
    #
    port = int(os.environ.get('PORT', PORT))
    app.run(host='0.0.0.0', port=port)
    #
    # red = [get_color(f"/tests/red/{f}") for f in os.listdir("/tests/red/")]
    # green = [get_color(f"/tests/green/{f}") for f in os.listdir("/tests/green/")]
    # print(*green, sep="\n")

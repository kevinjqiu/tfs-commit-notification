from subprocess import Popen, PIPE
from sys import stdout as STDOUT
from datetime import datetime

import re
import threading
import time


PATTERN = re.compile(r"^(\d+)\s+([\w\.]+)\s+(\d{1,2}\/\d{1,2}\/\d{4})(.+)$")


def hours(h):
    return h * minutes(60)

def minutes(m):
    return m * 60

class Changeset(object):
    def __init__(self, line):
        m = re.search(PATTERN, line)
        if (m):
            self.id, self.user, self.date, self.comments = m.groups()
            self.id = int(self.id)
        else:
            raise StandardError("Cannot match: %s" % line)

    def __str__(self):
        return "(%s) %s: %s %s" % (self.date, self.id, self.user, self.comments)

    def __gt__(self, other):
        return self.id > other.id

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id

    __repr__ = __str__

class TimePeriod(object):

    def __init__(self, start, end):
        """start and end are of the form: (hour_of_day,[minute[,second]])
        """

        self.start = (start[0], len(start) > 1 and start[1] or 0, len(start) > 2 and start[2] or 0)
        self.end = (end[0], len(end) > 1 and end[1] or 59, len(end) > 2 and end[2] or 59)

    def _flatten(self, datetime):
        return hours(datetime[0]) + minutes(datetime[1]) + datetime[2]

    def contains(self, datetime):
        time = self._flatten(datetime.timetuple()[3:6])
        return self._flatten(self.start) <= time <= self._flatten(self.end)

class IntervalPolicy(object):
    """Determines the pull interval at a particular time of day
    """

    def __init__(self):
        self.default_pull_interval = minutes(30)
        self.weekend_pull_interval = hours(5)
        self.pull_interval = {
            TimePeriod((0,), (8,)):hours(1),
            TimePeriod((9,), (12,)):minutes(5),
            TimePeriod((13,), (16,)):minutes(10),
            TimePeriod((17,), (23,)):hours(1),}

    def getInterval(self, current_time):
        if current_time.weekday() in (5, 6):
            return self.weekend_pull_interval
        else:
            for timeperiod in self.pull_interval:
                if timeperiod.contains(current_time):
                    return self.pull_interval[timeperiod]

        return self.default_pull_interval


class Agent(threading.Thread):
    DEFAULT_INTERVAL = 60

    def __init__(self, tfs_cmd, path, stdout=STDOUT, interval_policy=IntervalPolicy(), notification=None):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        self.tfs = tfs_cmd
        self.path = path
        self.interval_policy = interval_policy
        self.stdout = stdout
        self.latest = None
        self.notification = notification
        self.command = " ".join((self.tfs, "history", path, "/noprompt", "/recursive"))

    def setLatest(self, latest):
        self.latest = latest
        if self.notification == None:
            print >> self.stdout, "<%s>" % self, latest
        else:
            self.notification(latest)

    def run(self):
        while True:
            p = Popen(self.command, stdout=PIPE)
            child_out = p.stdout
            head = child_out.read().split("\r\n")[2]

            cur = Changeset(head)
            if not self.latest:
                self.setLatest(cur)
            elif self.latest < cur:
                self.setLatest(cur)
            child_out.close()

            interval = self.getInterval()
            print "Current pull interval: ", interval
            time.sleep(interval)

    def getInterval(self):
        if self.interval_policy is None:
            return self.DEFAULT_INTERVAL
        else:
            now = datetime.now()
            return self.interval_policy.getInterval(now)

    def __str__(self):
        return self.path


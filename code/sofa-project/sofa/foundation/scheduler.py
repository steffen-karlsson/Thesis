# Created by Steffen Karlsson on 06-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import getLogger, ERROR

from apscheduler.schedulers.background import BackgroundScheduler

getLogger('apscheduler.executors.default').setLevel(ERROR)
getLogger('apscheduler.scheduler.default').propagate = False

getLogger('apscheduler.scheduler').setLevel(ERROR)
getLogger('apscheduler.scheduler').propagate = False


class BackgroundDaemonScheduler(BackgroundScheduler):
    def shutdown(self, wait=True):
        try:
            super(BackgroundDaemonScheduler, self).shutdown(wait)
        except RuntimeError:
            # Apscheduler mistakenly joins if its current thread which causes RuntimeError
            pass

        del self._thread

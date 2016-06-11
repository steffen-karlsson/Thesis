# Created by Steffen Karlsson on 06-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from apscheduler.schedulers.background import BackgroundScheduler


class BackgroundDaemonScheduler(BackgroundScheduler):
    def shutdown(self, wait=True):
        try:
            super(BackgroundDaemonScheduler, self).shutdown(wait)
        except RuntimeError:
            # Apscheduler mistakenly joins if its current thread which causes RuntimeError
            pass

        del self._thread

# Copyright 2012 David Fendrich

# This file is part of Selfspy

# Selfspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Selfspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Selfspy.  If not, see <http://www.gnu.org/licenses/>.

import bisect


class Period:
    def __init__(self, cutoff, maxtime):
        self.times = []
        self.cutoff = cutoff
        self.maxtime = maxtime

    def append(self, time):
        ltimes = len(self.times)
        end = min(time + self.cutoff, self.maxtime)

        def check_in(i):
            if self.times[i][0] <= time <= self.times[i][1]:
                self.times[i] = (self.times[i][0], max(end, self.times[i][1]))
                return True
            return False

        def maybe_merge(i):
            if ltimes > i + 1:
                if self.times[i][1] >= self.times[i + 1][0]:
                    self.times[i] = (self.times[i][0], self.times[i + 1][1])
                    self.times.pop(i + 1)

        if ltimes == 0:
            self.times.append((time, end))
            return

        i = bisect.bisect(self.times, (time,))
        if i >= 1 and check_in(i - 1):
            maybe_merge(i - 1)
        elif i < ltimes and check_in(i):
            maybe_merge(i)
        else:
            self.times.insert(i, (time, end))
            maybe_merge(i)

    def extend(self, times):
        for time in times:
            self.append(time)

    def calc_total(self):
        return sum(t2 - t1 for t1, t2 in self.times)

#merge to intervals immediately

class Period:
    def __init__(self):
        self.times = []

    def extend(self, times):
        self.times.extend(times)

    def calc_total(self, cutoff):
        self.times.sort()
        tot = 0

        last = -cutoff
        for t in self.times:
            tot += max(min(t - last, cutoff), 0)
            last = t
        return tot

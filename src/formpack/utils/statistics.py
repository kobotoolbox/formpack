# -*- coding: utf-8 -*-
import statistics


def singlemode(data):
    try:
        # New in Python 3.8
        modes = statistics.multimode(data)
    except AttributeError:
        return statistics.mode(data)
    else:
        if len(modes) > 1:
            raise statistics.StatisticsError('no unique mode')
        else:
            return modes[0]

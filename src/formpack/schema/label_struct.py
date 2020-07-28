# LabelStruct is a class that holds translated values

class LabelStruct:
    def __init__(self, label, txs):
        self._label = label
        _labels = []
        self._txs = txs
        self._txnames = [tx['name'] for tx in txs]
        for tx in txs:
            _labels.append(self._label.get(tx['$anchor']))
        self._labels = _labels

    def get(self, key, _default):
        if key is None:
            key = ''
        if key is False:
            return _default
        else:
            _i = self._txnames.index(key)
            return self._labels[_i]


class NoLabelStruct:
    def __init__(self, *_args):
        self._args = _args
        self._labels = []

    def get(self, key, _default):
        return _default

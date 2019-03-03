class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def read(path):
    r = AttrDict()
    with open(path) as f:
        for line in f:
            s = line.split('#', 1)[0]
            if s:
                kv = s.split(' ', 1)
                if len(kv) == 2:
                    k, v = [x.strip() for x in kv]
                    r[k] = v
    return r

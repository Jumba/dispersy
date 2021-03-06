from atexit import register
from bz2 import BZ2File
from time import time
import re


def _encode_str(l, value):
    assert isinstance(l, list)
    assert isinstance(value, str)
    for char in value:
        if not char in _printable:
            value = value.encode("HEX")
            l.extend(("h", str(len(value)), ":", value))
            break
    else:
        l.extend(("s", str(len(value)), ":", value))


def _encode_unicode(l, value):
    value = value.encode("UTF-8")
    for char in value:
        if not char in _printable:
            value = value.encode("HEX")
            l.extend(("H", str(len(value)), ":", value))
            break
    else:
        l.extend(("u", str(len(value)), ":", value))


def _encode_int(l, value):
    l.extend(("i", str(value)))


def _encode_long(l, value):
    l.extend(("j", str(value)))


def _encode_float(l, value):
    l.extend(("f", str(value)))


def _encode_boolean(l, value):
    l.extend(("b", value and "True" or "False"))


def _encode_none(l, value):
    l.append("nNone")


def _encode_tuple(l, values):
    if values:
        l.extend(("t", str(len(values)), ":", "("))
        for value in values:
            _encode(l, value)
            l.append(", ")
        l[-1] = ")"
    else:
        l.append("t0:()")


def _encode_list(l, values):
    if values:
        l.extend(("l", str(len(values)), ":", "["))
        for value in values:
            _encode(l, value)
            l.append(", ")
        l[-1] = "]"
    else:
        l.append("l0:[]")


def _encode_dict(l, values):
    if values:
        l.extend(("m", str(len(values)), ":", "{"))
        for key, value in values.iteritems():
            _encode(l, key)
            l.append(":")
            _encode(l, value)
            l.append(", ")
        l[-1] = "}"
    else:
        l.append("m0:{}")


def _encode(l, value):
    if type(value) in _encode_mapping:
        _encode_mapping[type(value)](l, value)
    else:
        raise ValueError("Can not encode %s" % type(value))


def log(filename, _message, **kargs):
    assert isinstance(_message, str)
    assert ";" not in _message

    global _encode_initiated
    if _encode_initiated:
        l = ["{0:.6f}".format(time()), _seperator]
    else:
        _encode_initiated = True
        l = ["################################################################################", "\n",
             "{0:.6f}".format(time()), _seperator, "s6:logger", _seperator, "event:s5:start", "\n",
             "{0:.6f}".format(time()), _seperator]

    _encode_str(l, _message)
    for key in sorted(kargs.keys()):
        l.append(_seperator)
        l.extend((key, ":"))
        _encode(l, kargs[key])
    l.append("\n")
    s = "".join(l)

    # save to file
    open(filename, "a+").write(s)


def bz2log(filename, _message, **kargs):
    assert isinstance(_message, str)
    assert ";" not in _message

    global _cache, _encode_initiated
    handle = _cache.get(filename)
    if _encode_initiated:
        l = ["{0:.6f}".format(time()), _seperator]
    else:
        _encode_initiated = True
        l = ["################################################################################", "\n",
             "{0:.6f}".format(time()), _seperator, "s6:logger", _seperator, "event:s5:start", "\n",
             "{0:.6f}".format(time()), _seperator]
        handle = BZ2File(filename, "w", 8 * 1024, 9)
        register(handle.close)
        _cache[filename] = handle

    _encode_str(l, _message)
    for key in sorted(kargs.keys()):
        l.append(_seperator)
        l.extend((key, ":"))
        _encode(l, kargs[key])
    l.append("\n")
    s = "".join(l)

    # write to file
    handle.write(s)

    return handle


def make_valid_key(key):
    return re.sub('[^a-zA-Z0-9_]', '_', key)

_printable = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ "
_seperator = "   "
_valid_key_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
_cache = {}
_encode_initiated = False
_encode_mapping = {str: _encode_str,
                   unicode: _encode_unicode,
                   int: _encode_int,
                   long: _encode_long,
                   float: _encode_float,
                   bool: _encode_boolean,
                   type(None): _encode_none,
                   tuple: _encode_tuple,
                   list: _encode_list,
                   dict: _encode_dict}

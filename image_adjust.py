from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
from math import sqrt
import argparse

DEFAULT_DARKEN = 4.7
DEFAULT_HIGHLIGHTS = 8
DEFAULT_MIDTONES = 20
DEFAULT_CONTRAST = 2.7


class Adjuster(object):

    def __init__(self, hl, mt, darken):
        self.hl = hl
        self.mt = mt
        self.darken = darken

    def stretch(self, i, min, max):
        min_delta = i - min
        max_delta = max - i
        if min_delta == max_delta:
            return i
        if min_delta > max_delta:
            return int(i - sqrt((min / min_delta)) * self.mt)
        if max_delta > min_delta:
            return int (i + sqrt((max / max_delta)) * self.hl)
            
    def apply_darkening(self, i, min):
        delta = i - min
        if delta > 0:
            return max(min, i - int(sqrt(delta) * self.darken))
        return i

    def apply_clarity(self, i):
        if i < 10:
            return 0
        if i > 200:
            return self.stretch(i, 0, 255)
        if i > 100:
            return self.stretch(i, 0, 200)
        return self.stretch(i, 0, 100)

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("file_path")
parser.add_argument("-d", "--darken", action="store")
parser.add_argument("-hl", "--highlights", action="store")
parser.add_argument("-m", "--midtones", action="store")
parser.add_argument("-detail", "--detail", action="store_true")
parser.add_argument("-c", "--contrast", action="store")
args = parser.parse_args()

# read argument values or use defaults
try:
    darken_value = float(getattr(args, "darken"))
except:
    print("Using default darken value", DEFAULT_DARKEN)
    darken_value = DEFAULT_DARKEN
try:
    hl_value = float(getattr(args, "highlights"))
except:
    print("Using default highlights value", DEFAULT_HIGHLIGHTS)
    hl_value = DEFAULT_HIGHLIGHTS
try:
    mt_value = float(getattr(args, "midtones"))
except:
    print("Using default midtones value", DEFAULT_MIDTONES)
    mt_value = DEFAULT_MIDTONES
try:
    contrast_value = float(getattr(args, "contrast"))
except:
    print("Using default contrast value", DEFAULT_CONTRAST)
    contrast_value = DEFAULT_CONTRAST

adjuster = Adjuster(hl_value, mt_value, darken_value)
    
with Image.open(args.file_path) as im:
    if args.detail:
        im = im.filter(ImageFilter.DETAIL)
    im = im.point(lambda i: adjuster.apply_darkening(i, 0))
    im = im.point(lambda i: adjuster.apply_clarity(i))
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(2.7)
    im.save("result.jpeg")
    
from PIL import Image, ImageDraw, ImageFont

def newFrame(size):
    canvas = Image.new("RGB",size)
    return canvas

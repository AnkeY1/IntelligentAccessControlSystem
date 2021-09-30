import sensor, image, lcd, time
import KPU as kpu
from machine import I2C
import ustruct

color_R = (255, 0, 0)
color_G = (0, 255, 0)
color_B = (0, 0, 255)


class_IDs = ['no_mask', 'mask']

i2c_address = 0x69
register = 0x80
i2c = I2C(I2C.I2C0, freq=100000, scl=32, sda=33)
img8 = [[0 for x in range(0, 8)] for x in range(0,8)]



def getval(val):
  absval = (val & 0x7FF)
  if val & 0x800:
    return - float(0x800 - absval) * 0.25
  else:
    return float(absval) * 0.25


def getTempArray(mat):
    image_x = -1;
    image_y = 0;

    reg = register
    for i in range(0, 64):
        val = ustruct.unpack('<h', i2c.readfrom_mem(i2c_address, reg, 2))[0]
        tmp = getval(val)
        if(i % 8 == 0):
            image_x = image_x + 1
            image_y = 0
        else:
            image_y = image_y + 1
        mat[image_x][image_y] = tmp
        #(str(image_x) + " " + str(image_y) + " " + str(tmp))
        reg += 2


def drawConfidenceText(image, rol, classid, value):
    text = ""
    _confidence = int(value * 100)
    if classid == 1:
        text = 'mask: ' + str(_confidence) + '%'
        color_text=color_G
        if temperature2<36.0 or temperature2>37.5:
            img.draw_string(10, 200,str(temperature2) , color = (255, 0,
                            0), scale = 2,mono_space = False)
        else:
            img.draw_string(10, 200,str(temperature2) , color = (0, 255,
                            0), scale = 2,mono_space = False)
    else:
        text = 'no_mask: ' + str(_confidence) + '%'
        color_text=color_R
        if temperature2<36.0 or temperature2>37.5:
            img.draw_string(10, 200,str(temperature2) , color = (255, 0,
                            0), scale = 2,mono_space = False)
        else:
            img.draw_string(10, 200,str(temperature2) , color = (0, 255,
                            0), scale = 2,mono_space = False)
    image.draw_string(rol[0], rol[1], text, color=color_text, scale=2.5)

lcd.init()
sensor.reset(dual_buff=True)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(1)
sensor.run(1)


task = kpu.load(0x300000)


anchor = (0.1606, 0.3562, 0.4712, 0.9568, 0.9877, 1.9108, 1.8761, 3.5310, 3.4423, 5.6823)
_ = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)
img_lcd = image.Image()

clock = time.clock()
while (True):
    clock.tick()
    img = sensor.snapshot()
    code = kpu.run_yolo2(task, img)
    getTempArray(img8)
    temperature2 = 34.5+pow(2,(img8[3][3]/24+img8[3][4]/24+img8[4][3]/24+img8[4][4]/24)/4)
    if code:
        totalRes = len(code)

        for item in code:
            confidence = float(item.value())
            itemROL = item.rect()
            classID = int(item.classid())

            if confidence < 0.52:
                _ = img.draw_rectangle(itemROL, color=color_B, tickness=5)
                continue

            if classID == 1 and confidence > 0.65:
                _ = img.draw_rectangle(itemROL, color_G, tickness=5)
                if totalRes == 1:
                    drawConfidenceText(img, (0, 0), 1, confidence)
            else:
                _ = img.draw_rectangle(itemROL, color=color_R, tickness=5)
                if totalRes == 1:
                    drawConfidenceText(img, (0, 0), 0, confidence)

    _ = lcd.display(img)

    print(clock.fps())

_ = kpu.deinit(task)

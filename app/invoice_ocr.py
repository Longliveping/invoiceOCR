import pandas as pd
from splinter import Browser
import time
import pyperclip
# import cv2
# import numpy as np
# from pyzbar.pyzbar import decode
from paddleocr import PaddleOCR
from PIL import Image
import re

def crop_image(img_path):
    img = Image.open(img_path)
    x_len = img.size[0]
    y_len = img.size[1]
    if x_len > y_len:
        area = (x_len*0.7,0,x_len,y_len*0.2)
    else:
        area = (x_len*0.7,y_len*0.5,x_len,y_len)
    cropped_fp = img.crop(area) # (left, upper, right, lower)
    print('crop:',img.size, area)
    cropped_fp.save('fp_crop.png')

def ocr_image(img_path, rotate=False):
    img = Image.open(img_path)
    if img.size[0] < img.size[1] or rotate:
        transposed = img.transpose(Image.ROTATE_90)
        transposed.save(img_path)
    # 同样也是通过修改 lang 参数切换语种
    ocr = PaddleOCR() # 首次执行会自动下载模型文件
    result = ocr.ocr(img_path)
    return result

def check_fp(ocr_result):
    passed = [False,False,False,False,False] # 发票代码, 发票号码, 开票日期, 校验码, 金额
    fp = ['','','','',0]
    fp0 = dict()

    for i, line in enumerate(ocr_result):
        print(i, line)
        # print(i, line[-1][0])
        s = str(line[-1][0])

        # if '小写' in s:
        #     n = re.search(r'￥(\d+.\d+)',s)
        #     if n:
        #         fp[4] = float(m.group(1))
        # else:
        m = re.search(r'￥(\d+.\d+)',s)
        if m:
            if fp[4] < float(m.group(1)):
                fp[4] = float(m.group(1))

        try:
            fp0[s.split('：')[0]] = s.split('：')[1]
        except:
            pass

    try:
        fp[0] = fp0['发票代码']
        fp[1] = fp0['发票号码']
        fp[2] = fp0['开票日期'][:4]+fp0['开票日期'][5:7]+fp0['开票日期'][8:10]
        fp[3] = fp0['校验码'][-6:]
    except:
        pass

    passed[0] = len(fp[0]) == 12 and fp[0].isdigit()
    passed[1] = len(fp[1]) == 8 and fp[0].isdigit()
    passed[2] = len(fp[2]) == 8 and fp[0].isdigit()
    passed[3] = len(fp[3]) == 6 and fp[0].isdigit()
    passed[4] = float(fp[4]) > 0

    return passed, fp

def invoice_data(img_path, rotate=False):
    result = ocr_image(img_path,rotate)
    # 可通过参数控制单独执行识别、检测
    # result = ocr.ocr(img_path, det=False) 只执行识别
    # result = ocr.ocr(img_path, rec=False) 只执行检测
    # 打印检测框和识别结果
    passed, fp = check_fp(result)
    print(0, passed)

    i = 0
    trues = [t for t in passed if t]
    while len(trues) < (len(passed) - len(trues)) and i < 3:
        result = ocr_image(img_path,rotate=True)
        passed, fp = check_fp(result)
        trues = [t for t in passed if t]
        i += 1
        print(i, passed)


    if len(set(passed)) == 1 and passed[0]:
        print('all set',passed, fp)
    else:
        crop_image(img_path)
        crop_img_path = '../fp_crop.png'
        result = ocr_image(crop_img_path)
        passed_crop, fp_crop = check_fp(result)
        for i, t in enumerate(passed):
            if not t and passed_crop[i]:
                passed[i] = True
                fp[i] = fp_crop[i]

    if len(set(passed)) == 1 and passed[0]:
        print('all set', fp)
        df = pd.Series(fp)
        df.to_csv('invoice.csv')
        return True
    else:
        print('still to come:', passed, fp)
        return False


    # 可视化
    # from PIL import Image
    # image = Image.open(img_path).convert('RGB')
    # boxes = [line[0] for line in result]
    # txts = [line[1][0] for line in result]
    # scores = [line[1][1] for line in result]
    # im_show = draw_ocr(image, boxes, txts, scores,font_path='chinese_cht.ttf')
    # im_show = Image.fromarray(im_show)
    # im_show.save('result.jpg')

def invoice_verify():
    df = pd.read_csv('../invoice.csv', index_col=0, dtype=str)
    invoice_code        = df.iat[0,0]
    invoice_number      = df.iat[1,0]
    invoice_date        = df.iat[2,0]
    invoice_checksum    = df.iat[3,0]
    invoice_sum         = df.iat[4,0]
    print(invoice_code, invoice_number,invoice_date, invoice_checksum, invoice_sum)

    executable_path = {'executable_path': '/usr/local/bin/chromedriver'}
    browser = Browser('chrome',**executable_path,user_agent="Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en)")
    browser.visit('http://inv-veri.com/')
    browser.find_by_xpath('//*[@id="app"]/form/div[1]/div/div/input').fill(invoice_code)
    browser.find_by_xpath('//*[@id="app"]/form/div[2]/div/div/input').fill(invoice_number)
    browser.find_by_xpath('//*[@id="app"]/form/div[3]/div/div/input').fill(invoice_date)
    browser.find_by_xpath('//*[@id="app"]/form/div[4]/div/div/input').fill(invoice_checksum)
    browser.find_by_xpath('//*[@id="app"]/form/div[3]/label').click()
    time.sleep(0.2)
    browser.find_by_xpath('//*[@id="app"]/form/div[7]/div/button[1]').click()
    time.sleep(5)
    browser.find_by_xpath('//*[@id="app"]/form/div[7]/div/button[3]').click()

    clip = pyperclip.paste()
    df = pd.read_json(clip)
    df.to_csv('verify.csv')
    df.to_json('verify.json')
    # print(df)
    # browser.quit()
    if len(df) > 15:
        print('发票验证通过')
        return True
    else:
        return False


if __name__ == '__main__':
    img_path = '../fp00.jpeg'
    if invoice_data(img_path):
        pass
        invoice_verify()



import pandas as pd
from splinter import Browser
import time
import pyperclip
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

def check_type(ocr_result):
    for i, line in enumerate(ocr_result):
        # print(i, line)
        # print(i, line[-1][0])
        s = str(line[-1][0])
        if '普通' in s or '校验码' in s:
            return '普通发票'
        if '专用发票' in s or '第二联' in s or '第一联' in s or '凭证' in s or '抵扣' in s or '记账' in s:
            return '专用发票'
    return ''

def check_fp(ocr_result, passed, fp):
    fp0 = dict()

    if not passed[0]:
        fp[0] = check_type(ocr_result)
        if fp[0]: passed[0] = True

    for i, line in enumerate(ocr_result):
        print(i, line)
        # print(i, line[-1][0])
        s = str(line[-1][0])

        if not passed[5] or not passed[6]:
            m = re.search(r'(\d+\.\d\d)',s)
            if m:
                f = float(m.group(1))
                if f > float(fp[6]):
                    fp[6] = f
                elif f > float(fp[5]):
                    fp[5] = f

        if (len(s) == 10 or len(s) == 12) and s.isdigit():
            fp0['发票代码_'] = s
        if len(s) == 8 and s.isdigit():
            fp0['发票号码_'] = s
        if len(s) == 11 and '年' in s:
            fp0['开票日期_'] = s

        try:
            fp0[s.split('：')[0]] = s.split('：')[1]
        except:
            pass


    print('\n', fp0)

    if not passed[1]:
        try:
            fp[1] = fp0['发票代码']
            passed[1] = ((len(fp[1]) == 12) or (len(fp[1]) == 10)) and fp[1].isdigit()
            if not passed[1]: fp[1] = ''
        except:
            pass

    if not passed[1]:
        try:
            fp[1] = fp0['发票代码_']
            passed[1] = ((len(fp[1]) == 12) or (len(fp[1]) == 10)) and fp[1].isdigit()
            if not passed[1]: fp[1] = ''
        except:
            pass

    if not passed[2]:
        try:
            fp[2] = fp0['发票号码']
            passed[2] = len(fp[2]) == 8 and fp[2].isdigit()
            if not passed[2]: fp[2] = ''
        except:
            pass

    if not passed[2]:
        try:
            fp[2] = fp0['发票号码_']
            passed[2] = len(fp[2]) == 8 and fp[2].isdigit()
            if not passed[2]: fp[2] = ''
        except:
            pass


    if not passed[3]:
        try:
            fp[3] = fp0['开票日期'][:4]+fp0['开票日期'][5:7]+fp0['开票日期'][8:10]
            passed[3] = len(fp[3]) == 8 and fp[3].isdigit()
            if not passed[3]: fp[3] = ''
        except:
            pass

    if not passed[3]:
        try:
            fp[3] = fp0['开票日期_'][:4]+fp0['开票日期_'][5:7]+fp0['开票日期_'][8:10]
            passed[3] = len(fp[3]) == 8 and fp[3].isdigit()
            if not passed[3]: fp[3] = ''
        except:
            pass

    if not passed[4]:
        try:
            fp[4] = fp0['校验码'][-6:]
            passed[4] = len(fp[4]) == 6 and fp[4].isdigit()
            if not passed[4]: fp[4] = ''
        except:
            pass

    passed[5] = float(fp[5]) > 0
    passed[6] = float(fp[6]) > 0


def invoice_data(img_path, rotate=False):
    passed = [False, False,False,False,False,False,False] # 发票类型, 发票代码, 发票号码, 开票日期, 校验码, 金额, 价税合计
    fp = ['','','','','',0.00,0.00]
    #开始识别
    result = ocr_image(img_path,rotate)
    check_fp(result, passed, fp)
    print(0, passed, fp)

    # 识别率过低则旋转图片,找到识别率比较高的角度
    i = 0
    trues = [t for t in passed if t]
    while len(trues) < (len(passed) - len(trues)) and i < 3:
        result = ocr_image(img_path,rotate=True)
        check_fp(result, passed, fp)
        trues = [t for t in passed if t]
        i += 1
        print(i, passed, fp)

    # 普票未全部识别则局部放大识别
    if len(set(passed)) == 1 and passed[0]:
        print('all set',fp)
    elif fp[0] == '普通发票':
        crop_image(img_path)
        crop_img_path = 'fp_crop.png'
        result = ocr_image(crop_img_path)
        check_fp(result, passed, fp)

    # 未识别发票类型则旋转图片,找到识别率比较高的角度
    i = 0
    while i < 3 and not passed[0]:
        result = ocr_image(img_path,rotate=True)
        check_fp(result, passed, fp)
        i += 1
        print(i, passed, fp)

    #保存识别结果
    df = pd.Series(fp)
    df.to_csv('invoice.csv')

    # 打印识别结果
    if len(set(passed)) == 1 and passed[0]:
        print('all set', fp)
    else:
        print('still to come:', passed, fp)

    return passed, fp

    # 可视化
    # from paddleocr import draw_ocr
    # image = Image.open(img_path).convert('RGB')
    # boxes = [line[0] for line in result]
    # txts = [line[1][0] for line in result]
    # scores = [line[1][1] for line in result]
    # im_show = draw_ocr(image, boxes, txts, scores,font_path='chinese_cht.ttf')
    # im_show = Image.fromarray(im_show)
    # im_show.save('result.jpg')


def invoice_verify():
    df = pd.read_csv('../data/invoice.csv', index_col=0, dtype=str)
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
    img_path = 'fp00.jpeg'
    if invoice_data(img_path):
        pass
        invoice_verify()



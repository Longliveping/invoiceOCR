FROM registry.baidubce.com/paddlepaddle/paddle:2.0.0

RUN pip3.7 install --upgrade pip -i https://mirror.baidu.com/pypi/simple

RUN git clone https://github.com/Longliveping/invoiceOCR.git /invoiceOCR

WORKDIR /invoiceOCR

RUN pip3.7 install -r requirements.txt -i https://mirror.baidu.com/pypi/simple

CMD ["python3", "/app/main.py" ]
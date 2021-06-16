FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY ./app /app

COPY ./requirements.txt /requirements.txt

WORKDIR /

RUN pip install -r requirements.txt -i https://mirror.baidu.com/pypi/simple

ENTRYPOINT [ "python3" ]

CMD [ "app/main.py" ]
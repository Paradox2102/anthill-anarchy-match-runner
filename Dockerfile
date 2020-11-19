FROM python:3.8.2-alpine3.11
WORKDIR /usr/src/app

RUN apk add --no-cache \
    build-base libffi-dev\
    && pip install gevent==20.9.0 \
    && apk del build-base

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#CMD ["gunicorn", "--bind", "0.0.0.0:80", "-w", "4", "--timeout", "1200", "--preload", "app:app"]
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]
EXPOSE 80
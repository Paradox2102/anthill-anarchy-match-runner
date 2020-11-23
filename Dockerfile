FROM python:3.8.2-alpine3.11
WORKDIR /usr/src/app

# Suppress warning
RUN pip install --upgrade pip

# eventlet is used to make websockets performant.  
# It requires GCC, which is not part of the python base image.
# We delete after installation to keep the image smaller.
RUN apk update \
    && apk add --no-cache build-base libffi-dev\
    && pip install eventlet==0.28.1 \
    && apk del build-base libffi-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python" ]
CMD [ "app.py" ]
EXPOSE 80
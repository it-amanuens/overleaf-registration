FROM python:alpine

RUN apk add --no-cache tzdata

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
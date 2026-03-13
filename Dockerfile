FROM python:slim

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "-c", "gunicorn wsgi:app --bind 0.0.0.0:8000 --env OL_INSTANCE=$OL_INSTANCE --env OL_ADMIN_EMAIL=$OL_ADMIN_EMAIL --env OL_ADMIN_PASSWORD=$OL_ADMIN_PASSWORD"]
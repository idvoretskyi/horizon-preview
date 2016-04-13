FROM python:3.4

MAINTAINER Michael Glukhovsky, mike@rethinkdb.com

RUN apt-get update && \
    apt-get -y install nginx-full && \
    apt-get -y install build-essential python-dev python-pip supervisor && \
    apt-get -y install ruby ruby-dev && \
    apt-get -y autoremove && \
    apt-get -y autoclean && \
    pip install --upgrade pip && \
    pip install uwsgi && \
    gem install jekyll


# Set up the WSGI app
COPY uwsgi.ini /etc/uwsgi.ini

# Set up nginx
COPY nginx.conf /etc/nginx/sites-available/flask-app
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN ln -s /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/flask-app && \
    rm /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Supervisor manages running services
RUN mkdir -p /var/log/supervisor
COPY supervisor.conf /etc/supervisor/conf.d/

# Set up the app
COPY app/requirements.txt /var/www/app/requirements.txt
RUN pip install -r /var/www/app/requirements.txt

# Copy and generate assets for the app
ENV WUFOO_KEY=0XJN-NFD3-WAHO-03UV
COPY app/ /var/www/app/
COPY www/ /tmp/www
RUN jekyll build -s /tmp/www/ -d /var/www/app/static/

# Start services
CMD ["supervisord", "-n"]

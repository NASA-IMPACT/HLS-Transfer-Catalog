FROM python:3.7
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends\
    build-essential \
    software-properties-common \
    wget \
    zip \
    nginx \
    jq \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN mkdir /hls-transfer-catalog/
COPY requirements.txt /hls-transfer-catalog/requirements.txt

# install python package
RUN pip3 install -r /hls-transfer-catalog/requirements/ml.txt && \
    pip3 install -r /hls-transfer-catalog/requirements/production.txt

COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

WORKDIR /hls-transfer-catalog/

COPY . /hls-transfer-catalog/

ARG PORT
ARG SECRET
ARG FULL_API_BASE_URL

ENV FULL_API_BASE_URL=${FULL_API_BASE_URL}
ENV SECRET=${SECRET}
ENV PORT=${PORT}

EXPOSE 80

# CMD ["/usr/local/bin/gunicorn", "config.wsgi", "--bind", "0.0.0.0:8080", "--workers", "3"]
CMD ["/hls-transfer-catalog/gunicorn.sh"]

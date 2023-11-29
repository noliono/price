FROM python:3.10.13-bookworm

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update
RUN apt-get install -y wget bzip2 libxtst6 libgtk-3-0 libx11-xcb-dev libdbus-glib-1-2 libxt6 libpci-dev firefox-esr python3-xvfbwrapper
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

#CMD [ "python", "./your-daemon-or-script.py" ]

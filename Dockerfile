# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Install any needed packages 
RUN apt-get update
RUN apt-get -y install git
RUN mkdir app
RUN git clone -b 2022.02.04 https://github.com/yt-dlp/yt-dlp.git
RUN mv yt-dlp/yt_dlp /app/
RUN apt-get -y install make zip ffmpeg
#RUN make -C yt-dlp yt-dlp
RUN apt-get -y install wget
RUN pip install tweepy
RUN apt-get install nano
RUN pip install mutagen
RUN apt-get -y install procps
COPY worker.py /app
COPY appval.py /app
CMD python /app/worker.py

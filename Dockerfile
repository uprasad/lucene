FROM openjdk:24-bullseye

# Install packages
RUN apt-get update
RUN apt-get install -y strace
RUN apt-get install -y python3-distutils
RUN apt-get install -y wamerican

WORKDIR /home/

# Install pip and tqdm
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py
RUN python3 -m pip install tqdm
RUN rm get-pip.py

# Copy the JAR
COPY lucene.jar .
COPY lib/lucene-core-9.11.0.jar .

# Copy scripts
COPY src/scripts/strace_events.py .
COPY src/scripts/strace_events_viz.py .
FROM python:3
LABEL maintainer="tguicherd@bcit.ca"
RUN mkdir /app
# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./requirements.txt /app/requirements.txt
# Set the working director
WORKDIR /app
# Install dependencies
RUN pip3 install --no-cache-dir setuptools
RUN pip3 install -r requirements.txt
# Copy the source code
COPY . /app
# Change permissions and become a non-privileged user
RUN chown -R nobody:nogroup /app
USER nobody
# Tells on which port the service listens in the container
EXPOSE 8092
# Entrypoint = run Python
ENTRYPOINT [ "python3" ]
# Default = run app.py
CMD [ "app.py" ]
FROM python:3.9-slim-buster
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
# change symlinks of python
RUN python3 -m venv venv 
RUN cp --remove-destination venv/bin/python* .venv/bin/
RUN rm -rf venv

# set env vars
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD ["python3", "main.py"]

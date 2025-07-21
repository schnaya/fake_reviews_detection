FROM python:3.10
WORKDIR /app
COPY app/requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY ./common_lib /app/common_lib
COPY ./app /app
EXPOSE 8080
CMD ["python", "api.py"]
FROM python:3.9

COPY requirements.txt . 

RUN pip install --upgrade pip  \
&& pip install -r requirements.txt

WORKDIR /app

COPY app.py .

CMD ["python", "./app.py"] 
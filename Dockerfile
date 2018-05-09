FROM python:3.6

ADD taskbot.py /
ADD my_routinebot_files $HOME/my_routinebot_files

RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt .
COPY ./my_routinebot_files .
RUN pip install -r requirements.txt
COPY . .

CMD [ "python", "./taskbot.py" ]

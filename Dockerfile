FROM jjanzic/docker-python3-opencv

COPY reconize_digits.py ./templates/ /

ENV FLASK_APP /reconize_digits.py

RUN pip3 install imutils scipy Flask APScheduler \
&& groupadd -g 1000 -r appuser && useradd --no-log-init -r --uid 1000 --gid 1000 -g appuser appuser

USER appuser

CMD [ "python", "/reconize_digits.py" ]

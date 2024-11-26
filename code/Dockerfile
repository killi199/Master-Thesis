FROM python:3.12.7

ADD main_data.py .
ADD functions.py .
ADD github_repo_stars.csv .
ADD requirements.txt .

RUN pip install -r requirements.txt

CMD [ "python", "./main_data.py" ]

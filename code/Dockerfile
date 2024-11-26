FROM python:3.12.7

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y \
    git-quick-stats

ADD main_data.py .
ADD functions.py .
ADD github_repo_stars.csv .
ADD requirements.txt .

RUN pip install -r requirements.txt

CMD [ "python", "./main_data.py" ]

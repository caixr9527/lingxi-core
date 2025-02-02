# llmops-api

llmops-api

celery：celery -A app.http.app.celery worker --loglevel INFO --pool solo

db downgrade：flask --app app.http.app db downgrade

db migrate：flask --app app.http.app db migrate

db upgrate：flask --app app.http.app db upgrade

pipreqs：pipreqs --ignore env --force
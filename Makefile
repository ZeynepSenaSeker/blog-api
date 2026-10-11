.PHONY: serve migrate shell freeze

serve:
	python manage.py runserver

migrate:
	python manage.py makemigrations && python manage.py migrate

shell:
	python manage.py shell

freeze:
	pip freeze | sort > requirements.txt

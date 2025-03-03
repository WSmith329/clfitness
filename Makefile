virtualenv: activate
	virtualenv ../clfitness

activate:
	echo 'virtualenv must be activated manually using "source bin/activate"'

install:
	pip install -r requirements.txt

test:
	python -m pytest

test-cov:
	python -m pytest --cov --cov-report=html:coverage_re --cov-config=./tests/.coveragerc
	echo 'http://localhost:63342/clfitness/coverage_re/index.html'

requirements:
	pip freeze > requirements.txt

tailwind:
	python clfitness/manage.py tailwind start


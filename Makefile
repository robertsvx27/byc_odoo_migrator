.PHONY: dist test install clean twine auto-completion

install:
	pip3 install -e .

test:
	pytest tests --cov=./xomg_migration $(TEST_ARGS) -n=auto -vv
dist:
	python3 setup.py sdist
clean:
	git clean -fdx
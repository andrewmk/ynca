#!/bin/sh
pytest --cov=ynca tests/ --cov-report term-missing --cov-report html

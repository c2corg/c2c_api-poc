#!/bin/bash

python3 -m venv venv
.\venv\Scripts\activate
pip install --upgrade setuptools pip  # you may have a too old version of pip/setuptools
pip install -e .

#!/bin/bash

if [ -d "venv" ]; then # Check if folder A exists
echo "remove existing virtual environment..."
starta=$SECONDS
rm -rf venv # Delete the entire folder
enda=$SECONDS
echo "removal took $((enda-starta)) seconds"
fi

echo "create virtual environment..."
startb=$SECONDS
python -m venv venv # Start a python virtual environment
endb=$SECONDS
echo "creation took $((endb-startb)) seconds"

echo "activate virtual environment..."
startc=$SECONDS
source venv/bin/activate # Activate the python virtual environment
endc=$SECONDS
echo "activation took $((endc-startc)) seconds"

echo "update pip..."
startd=$SECONDS
python -m pip install --upgrade pip # Update pip
endd=$SECONDS
echo "pip update took $((endd-startd)) seconds"

echo "install dependencies..."
starte=$SECONDS
python -m pip install -r venv_requirement.txt
ende=$SECONDS

echo "install local directory..."
startf=SECONDS
python -m pip install .
endf=SECONDS

echo "removal took $((enda-starta)) seconds"
echo "creation took $((endb-startb)) seconds"
echo "activation took $((endc-startc)) seconds"
echo "pip update took $((endd-startd)) seconds"
echo "dependencies installation took $((ende-starte)) seconds"
echo "local installation took $((endf-startf)) seconds"
echo "overall took $((endf-starta)) seconds"


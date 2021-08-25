#!/bin/bash

# Script for running parsing tests.
# Must be run from projects root.

set -e

export PYTHONPATH=$PWD

cd tests/parsing/

for dir in $(find . -maxdepth 1 -mindepth 1 -type d);
do
	echo "********************************************************************************"
	echo "Running test $dir"
	echo "********************************************************************************"
	cd $dir
	python3 ../../../main.py -d -p packages.tmp bus.fbd
	sed '/Path/d' packages.tmp > packages.tmp.sed
	sed '/Path/d' packages.golden > packages.golden.sed
	cmp packages.golden.sed packages.tmp.sed
	rm packages.tmp
	rm *.sed
	cd ..
	echo
	done

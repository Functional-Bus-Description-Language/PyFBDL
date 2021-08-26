#!/bin/bash

# Script for running parsing tests.
# Must be run from projects root.

set -e

export PYTHONPATH=$PWD

cd tests/parsing/

echo -e "Running parsing tests\n"

echo -e "Testing valid constructs\n"
for dir in $(find valid/ -maxdepth 1 -mindepth 1 -type d);
do
	echo "********************************************************************************"
	echo "Running test $dir"
	echo "********************************************************************************"
	cd $dir
	python3 ../../../../main.py -p packages bus.fbd
	sed '/Path/d' packages > packages.sed
	sed '/Path/d' packages.golden > packages.golden.sed
	cmp packages.golden.sed packages.sed
	rm packages
	rm *.sed
	cd ../..
	echo
done

echo -e "\n\nTesting invalid constructs\n"
for dir in $(find invalid/ -maxdepth 1 -mindepth 1 -type d);
do
	echo "********************************************************************************"
	echo "Running test $dir"
	echo "********************************************************************************"
	cd $dir
	python3 ../../../../main.py bus.fbd > /dev/null 2>stderr || true
	grep -A100 '^Exception' stderr > stderr.grep
	cmp stderr.golden stderr.grep
	rm stderr stderr.grep
	cd ../..
	echo
done

echo -e "All \e[1;32mPASSED\e[0m!"

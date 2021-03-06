#!/usr/bin/env bash

if ! builtin type -P protoc &>/dev/null; 
then
	echo "Can't find protoc; try something like: sudo apt-get install protobuf-compiler"
	exit 1
else
	mkdir -p carousel-cpp
	protoc --python_out=rawe --cpp_out=carousel-cpp kite.proto
	protoc --python_out=rawe --cpp_out=carousel-cpp mhempc.proto
	echo "Successfully generated C and Python protobuf message interfaces"
fi

if ! builtin type -P hprotoc &>/dev/null; 
then
	echo "Not generating haskell protobuf interface since hprotoc not installed;"
	echo 'Try running "cabal install hprotoc"'
	exit 1
else
	(
	cd wtfviz
	hprotoc -I.. --haskell_out=src kite.proto
	hprotoc -I.. --haskell_out=src mhempc.proto
	)
	(
	cd plot-ho-matic
	hprotoc -I.. --haskell_out=src kite.proto
	hprotoc -I.. --haskell_out=src mhempc.proto
	)
	echo "Successfully generated haskell protobuf message interface"
fi

exit 0

# QChat
QChat is a simple distributed encrypted chat platform built
on SimulaQron that enables users to derive shared keys with
their peers using the purified BB84 protocol in the presence 
of an unauthenticated classical channel. The key derivation
protocol includes error correction utilizing Golay linear
codes and privacy amplification built on keyless fuzzy
extractors. The derived keys are used to encrypt messages
between two users using AES-GCM to guarantee authenticity and
 integrity. The unauthenticated classical channel is
 solutioned using a registry server that maintains RSA
 public information for users in the network, allowing peers
  to authenticate un-encrypted messages necessary for the 
  key establishment process.
  
 # Setup
 Begin by cloning the repo locally.

 ## Dependencies and Verification
 To install dependencies simply run:

    make python-deps

 To install dependencies and run tests run:

    make verify

 ## Building and Installation
 The qchat package can be built using:

    make build

 And can be built+installed using:

    make install

 ## Without installation
 QChat can also be used without building and installing the package.  To do so add the repo directory to your PYTHONPATH:

    export PYTHONPATH=$PYTHONPATH:/path/to/QChat/
 
 # RPC
 There is a basic RPC example located in the examples/rpc_demo directory.

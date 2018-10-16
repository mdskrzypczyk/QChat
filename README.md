# QChat
QChat is a simple distributed encrypted chat platform built
on Simulaqron that enables users to derive shared keys with
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
 Clone the repo and install the dependencies in the provided
 requirements.txt file using:
 
    pip install -r requirements.txt
    
 This project additionally requires [Simulaqron](https://github.com/StephanieWehner/SimulaQron),
 after setting up the Simulaqron project ensure that the Simulaqron
 folder is either within the src directory for QChat or perform
 the following:
 
    export PYTHONPATH=$PYTHONPATH:/path/to/dir/containing/Simulaqron
    
 # Getting Started
 After setting up the project you can test that everything is working
 by initializing the nodes for the Simulaqron network and running
 the examples provided in the src directory.
 
 # RPC
 There is a basic XML-RPC Server and Client located within the qchat example directory now.

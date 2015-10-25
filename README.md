# CompNet
Basic codes to test switch functionality using switchyard. 

Algorithm used for learning switch:
1) Start with empty table.
2) When frame arrive with destination & its not in table, broadcast frame to all ports.
3) Store src address from where the packet arrived.
4) Remove stale address.

Code for myswitch and test cases are provided.

Challenge is mentioned at:
https://github.com/jsommers/switchyard/blob/master/examples/exercises/learning_switch/learning_switch.rst 

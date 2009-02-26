The implementation is based on the 2006 CPA paper by Chalmers (paper
59, 'CSP for .NET based on JCSP'), the JCSP implementation, and on the
C++ CSP implementation (cppcsp-1.3.3-pre6). TODO: add version numbers.

The main goals of the implementation are:
- a simpler implementation than the current Java and C# implementations
- a working implementation that can be used for teaching
- a working implementation that can be used for experiments in clusters and display walls in Tromso

The first implementations will not implement all of the JCSP core,
since it's unclear for me yet whether this is
a) necessary in Python,
b) why the different constructs where made in the first place, and
c) how to do this cleanly. 
A more iterative approach will be followed.




Acknowledgements: 
- Thanks to Robert Brewer (rwb123@gmail.com) for patches adding 
  Timer, Buffered channels, etc... (see CHANGES). 
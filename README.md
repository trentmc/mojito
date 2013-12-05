MOJITO
======

MOJITO is a tool for analog circuit topology selection / topology design (synthesis). 

Topology selection tools must consider a broad variety of topologies such that an appropriate topology is selected, must easily adapt to new semiconductor process nodes, and readily incorporate new topologies. Topology design tools must allow for designers to creatively explore new topology ideas as rapidly as possible. Such tools should not impose new, untrusted topologies that have no logical basis. 

MOJITO supports both topology selection and design.  It takes in a pre-specified library of about 30 hierarchically-organized analog building blocks. This library defines thousands of possible different circuit opamp topologies from different combinations of the building blocks. The library is independent of process, and does not require input of behavioral models. Therefore, it only has to be specified once. However, designers can readily add new building block ideas to it. MOJITO efficiently globally searches this library's possible topologies and sizings by leveraging the hierarchical nature of the blocks. MOJITO returns ("synthesizes") topologies that are trustworthy by construction. MOJITO is multi-objective, i.e. it returns a set of sized topologies that collectively approximate an optimal performance tradeoff curve. Once a single MOJITO run is done at a process node, the results are stored as a database for future queries by other designers. Therefore MOJITO supports a "specs-in sized-topology-out" workflow with immediate turnaround.

Main MOJITO references
======================

BOOK: T. McConaghy, P. Palmers, P. Gao, M. Steyaert, and G.G.E. Gielen.  Variation-Aware Analog Structural Synthesis: A Computational Intelligence Approach.  Springer, 2009, ISBN 978-9048129058. http://www.amazon.com/Variation-Aware-Analog-Structural-Synthesis-Computational/dp/9048129052

TEVC PAPER: T. McConaghy, P. Palmers, M. Steyaert, and G.G.E. Gielen, Trustworthy genetic programming-based synthesis of analog circuit topologies using hierarchical domain-specific building blocks, IEEE Transactions on Evolutionary Computation 15(4), Aug. 2011, pp. 557-570. http://trent.st/content/2011-TEVC-mojito-ea.pdf

MORE INFO: http://trent.st/publications/

Authors
=======

MOJITO was written by:
 * Trent McConaghy, Solido Design Automation Inc. gtrent@gmail.com
 * Pieter Palmers

The original MOJITO code was written during the Trent's and Pieter's PhD studies at ESAT-MICAS, KU Leuven, Belgium, between 2005 and 2008.

Using the code
==============

 * To get started: ./help.py
 * You know your version is working if all the unit tests pass: ./runtests.py

Release notes
=============

The original code was only integrated (well, hacked) into hspice, for a specific process. It has not been tested recently. It will likely take a bit of hacking to work with your simulator and model files anyway. (Priority: integrate into ngspice.)

Extensions
==========
MOJITO had several extensions, listed below. If you would like code related to one of these extensions, please contact Trent.
 * MOJITO-R -- process variation aware, i.e. yield as an additional objective. Reference: T. McConaghy, P. Palmers, G.G.E. Gielen, and M. Steyaert, Variation-aware structural synthesis of analog circuits via hierarchical building blocks and structural homotopy, IEEE Transactions on Computer-Aided Design 28(9), Sept. 2009, pp. 1281-1294. http://trent.st/content/2009-TCAD-robust_mojito.pdf
 * MOJITO-N -- novelty exploration. Reference: T. McConaghy, P. Palmers, G.G.E. Gielen, and M. Steyaert, Genetic programming with reuse of known designs, in Genetic Programming Theory and Practice V, Edited by R. Riolo and B. Worzel, Chapter 10, Springer, 2007. http://trent.st/content/2007-GPTP-novelty_mojito.pdf
 * ISCLES -- stacking many tiny circuits to learn new input-output mappings (e.g. V-V or flash ADCs). Reference: P. Gao, T. McConaghy, and G.G.E. Gielen, ISCLEs: Importance sampled circuit learning ensembles for robust analog IC design, in Proc. Intern. Conference on Computer-Aided Design (ICCAD), San Jose, November 2008. [PDF]
 *  TAPAS -- speed up basic MOJITO using a MOEA/D variant. Reference: P. Palmers, T. McConaghy, M. Steyaert, and G.G.E. Gielen, Massively multi-topology sizing of analog integrated circuits, in Proc. Design Automation and Test in Europe (DATE), March 2009. http://trent.st/content/2009_DATE_mojito_tapas.pdf

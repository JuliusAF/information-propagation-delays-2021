## Calibrating the Performance and Security of Blockchains via Information Propagation Delays

Miners of a blockchain exchange information about blocks and
transactions with one another via a peer-to-peer (P2P) network.
The speed at which they learn of new blocks and transactions in the
network determines the likelihood of forks in the chain, which in
turn has implications for the efficiency as well as security of proof-
of-work (PoW) blockchains. Despite the importance of information
propagation delays in a blockchain’s peer-to-peer network, little is
known about them. The last known empirical study was conducted,
for instance, by Decker and Wattenhofer in 2013.

In this paper, we revisit the work of Decker and Wattenhofer on
information propagation delays in Bitcoin. We update their mea-
surement methodology to accommodate the changes made to the
P2P network protocols since 2013. We also expand our measure-
ment effort to include three other widely used blockchains, namely
Bitcoin Cash, Litecoin, and Dogecoin. We reveal that block propa-
gation delays have drastically reduced since 2013: The majority of
peers in all four blockchains learn of a newly mined block within
one second; the likelihood of forks is, consequently, low. Though
blockchains networks have become quite efficient (i.e., have low
delays), we observe that a significant number of nodes of these
blockchains are present in cloud-provider networks and, more im-
portantly, state-owned network providers; such deployments have
crucial security implications for blockchains.

### Source code

The source code for the modified observer nodes and helper scripts can be found [here](https://github.com/JuliusAF/information-propagation-delays-2021), which is hosted on Github. The observer nodes are modified full nodes for each respective blockchain and were forked in April 2021. These nodes have therefore not seen development since that time, and any issues that may have been found in the parent applications since then have not been fixed. These nodes were run on Ubuntu 16.04.

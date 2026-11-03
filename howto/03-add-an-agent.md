# Add an agent

An agent is another host that measures from where it sits. Adding one takes one command there, and there is no license or email on an agent. The free tier covers five agents, and the local one on your master counts as the first.

There are two ways to do it, and you pick based on who can reach whom.

If the agent host can reach the master, use the join command. The install summary on the master already printed it, and you can print a fresh one any time with sudo trcrd enroll-agent. It is a single line with a one-hour token and the master's certificate hash. Paste it on the new host. It installs the daemon, enrolls, starts the agent, and says: this host is enrolled and the agent is running. Nothing else to do here.

If the master can reach the agent but not the other way round, for example a branch office behind NAT, do it the other way. On the new host run the installer with the agent option. It prints a pairing code and a fingerprint, and the exact command to run on the master. Run that command on the master, and the master comes to the agent and enrolls it.

Either way, check with sudo trcrd agents on the master. The new host shows as up, with the number of probes it runs. The master also adds mesh probes between agents automatically, so the moment you have two agents you can see latency between your sites.

If the agent never shows up, the usual cause is the advertise address. It must be an address your agents can reach, with the enrollment port, and ports 8443 and 8444 must be open. The install summary told you what it chose, and the troubleshooting page covers the rest.

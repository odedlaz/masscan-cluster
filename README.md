MASSCAN-Cluster
===============

Efficient clustering of [MASSCAN](https://github.com/robertdavidgraham/masscan) results

Motivation
----------

**MASSCAN** does a wonderful job at scanning the entire internet randomly.  
I want to cluster the results by port, a feature that **MASSCAN** lacks. 

Usage
-----

Simply open your shell and write:  
```bash
$ /path/to/masscan-cluster/msc.sh /path/to/output-dir
```

MASSCAN-Cluster will use `$PWD/masscan.conf` as the config file.  
If you want to specify a different file, pass it:  
```bash
$ /path/to/masscan-cluster/msc.sh /path/to/output-dir /path/to/masscan.conf
```

MASSCAN-Cluster rotates the files every 100kb, with is configurable via the environment variable `MAX_FILESIZE_KB`.  
for instance, for `1mb` chunks:
```bash
$ MAX_FILESIZE_KB=1024 /path/to/masscan-cluster/msc.sh
```

How does it work?
-----------------

MASSCAN writes all its output to a file.
MASSCAN-Cluster creates a [named pipe](https://en.wikipedia.org/wiki/Named_pipe) for MASSCAN output-file,  
runs MASSCAN, then clusters the output by port using the `split` script.

# Blockchain Sharding POC

### Implementation of Parallel sharding

### Clone

`git clone https://github.com/glorisonlai/blockchain-sharding-poc`

### Pull from source:

`git pull`

### Setting up venv:

1. `pip install venv`
2. `python -m venv ./`

### Setting up Redis:

- #### Windows
  1.  `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux`
  2.  Reboot may be needed
  3.  Download Ubuntu 18.04 from Microsoft Store [here](https://www.microsoft.com/en-us/p/ubuntu-1804/9n9tngvndl3q?activetab=pivot:overviewtab)
  4.  Launch Ubuntu WSL
  5.  `sudo apt-get update && sudo apt-get upgrade && sudo apt-get install redis-server`
  6.  `redis-cli -v`
  7.  `sudo service redis-server restart`

### Run locally:

1. `source Scripts/activate`
2. `npm install`
3. Launch Ubuntu WSL
4. `redis-server`
5. `npm run dev`

### Stopping Redis

`sudo service redis-server stop`

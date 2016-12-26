#!/bin/bash
set -ueo pipefail

### functions ###

# scope +e inside the function
function set_masscan_caps() {
   set +e
   getcap /usr/bin/masscan | /bin/grep -E "net_admin.*net_raw|net_raw.*net_admin" &> /dev/null
   if [ $? -ne 0 ]; then
      echo "Adding needed caps for masscan to work unpriviledged"
      /usr/bin/sudo -H /bin/sh -c "setcap cap_net_raw,cap_net_admin=eip /usr/bin/masscan"
   fi
}

function get_ipaddr() {
   ip -4 addr show $1 | awk '/inet/ {print $2}' | cut -d/ -f1
}

function usage() {
    echo "Usage: $0 <output-directory> <config-file>"
    echo "output-directory: has to exist"
    echo "config-file: optional, fallback to \"$PWD/masscan.conf\""
}

### end of functions ###
output_dir=${1:-/path/to/nowhere}
config_file="$(readlink -f ${2:-$PWD/masscan.conf})"
temp_dir="/tmp/masscan"
iface=$(cat masscan.conf | awk -F'=' '/adapter/ {print$2}' | xargs)
echo "=== MASSCAN Cluster==="
echo "Interface: $iface ($(get_ipaddr $iface))"
echo "Configuration file: $config_file"
echo "Output Directory: $output_dir"
echo -e "Temporary Directory: $temp_dir\n"

# make sure the directory exists
if [ ! -d "$output_dir" ]; then
  echo -e "Output directory doesn't exist at: $output_dir\n"
  usage
  exit 1
fi

if [ ! -f $config_file ]; then
  echo -e "Configuration file doesn't exist at: $config_file\n"
  usage
  exit 1
fi

set_masscan_caps


# /tmp is mounted on tmpfs ;)
mkdir -p $temp_dir

# extract the output-filename
filename=$(cat masscan.conf | awk -F'=' '/output-filename/ {print $2}' | xargs)
filepath="$temp_dir/$filename"
# create the named pipe at filepath
if [ ! -p $filepath ]; then
   echo "Creating masscan named pipe at: $filepath"
   rm -f $filename # remove existing file if it exists
   /usr/bin/mkfifo $filepath
fi

echo -e "\n=== Configuration ==="
cat $config_file

# run the split without stdout
./split.py $filepath $temp_dir $output_dir 1> /dev/null &
pid=$!

# masscan needs root permissions to 
cd $temp_dir; /usr/bin/masscan -c $config_file

# wait until the split is done
wait $pid

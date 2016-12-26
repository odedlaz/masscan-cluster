#!/usr/bin/python
from __future__ import print_function
import os
import sys
import json
import stat
import shutil
from uuid import uuid4
from functools import partial

port_mapping = {}

max_file_size = int(os.environ.get("MAX_FILESIZE_KB", "100")) # default to 100 kbytes

def should_rotate(f):
   """
   check if the filesize exceeded max file size
   """
   fsize = f.tell() / 1024.0 # filesize in kb
   return fsize > max_file_size

def rotate(f, port, output_dir):
   """
   close the file and move it to another directory
   """
   f.close()
   port_dir = os.path.join(output_dir, str(port))

   if not os.path.isdir(port_dir):
      os.mkdir(port_dir)

   shutil.move(f.name,
               os.path.join(port_dir, str(uuid4())))

def consume(path, callback):
   """
   read all lines from file at path,
   and call 'callback' on each of them
   """ 
   with open(path, 'r') as f:
      for line in iter(f.readline, b''):
         try:
	    item = json.loads(line.strip(",\n"))
	    callback(item)
         except ValueError:
	    continue

def save(item, temp_dir, output_dir):
   """
   save item to directory
   """
   for port_item in item["ports"]:
      port = port_item["port"]

      # get the current file-object
      f = port_mapping.get(port)
      
      # rotate the file if it exeeded the max file size
      if f and should_rotate(f):
         rotate(f, port, output_dir)
         f = None

      # create the file if it doesn't exist
      # and buffer writes up to 10% of the max file size
      if not f:
         f = port_mapping[port] = open(os.path.join(temp_dir,
                                                    str(port)),
                                       'a', max_file_size / 10)

      # save the item to the file
      # each item is seperated by a new line
      data = dict(ip=item["ip"],
                  timestamp=item["timestamp"],
                  port=port_item)
     
      # data is seperated by new lines
      # and is as compact as possible
      json.dump(data, f, separators=(',', ':'))
      f.write("\n")
      print(data)

if __name__ == "__main__":
   print(len(sys.argv))
   if len(sys.argv) != 4 \
      or not os.path.exists(sys.argv[1]) \
      or not stat.S_ISFIFO(os.stat(sys.argv[1]).st_mode) \
      or not os.path.isdir(sys.argv[3]):
         print("{} <FIFO> <temp-dir> <output-directory>".format(sys.argv[0]),
               sys.stderr)
         sys.exit(1)

   temp_dir = sys.argv[2]
   if not os.path.isdir(temp_dir):
      os.mkdir(temp_dir)
   
   # when file needs to rotate,
   # it's moved to the output dir
   output_dir = sys.argv[3]

   consume(path=sys.argv[1],
           callback=partial(save,
                            temp_dir=temp_dir,
                            output_dir=output_dir))

   # close all remaining files
   for port, f in port_mapping.items():
      rotate(f, port, output_dir)

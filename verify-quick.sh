#!/bin/sh
spin -a $2
gcc -o pan -O2 -DVECTORSZ=4196 -DMEMLIM=$1 -DSAFETY -DCOLLAPSE pan.c
./pan
#!/bin/sh

 netstat -an|awk '/tcp/ {print $6}'|sort|uniq -c
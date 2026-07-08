#!/usr/bin/perl
use strict;
use warnings;

my $target_ip = "8.8.8.8"; 
my $interface = "wlan0";   

# Check connectivity silently
my $ping_result = system("ping -c 2 -W 5 $target_ip > /dev/null 2>&1");

# If the ping fails (returns a non-zero exit code), restart the interface
if ($ping_result != 0) {
    system("/sbin/ip link set $interface down");
    sleep(5);
    system("/sbin/ip link set $interface up");
}

system("mkdir /home/user/PROOF");

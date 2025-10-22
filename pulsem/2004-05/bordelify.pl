#!/usr/bin/perl

# this script mixes up a list read from file or std input. It would 
# write it to stdout. The script has to store it, so that it can't be 
# infinitely long ...

@X = <>;
@X = sort { rand() <=> rand() } @X;
print @X; 

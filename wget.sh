#!/usr/bin/env bash

for n in {0..1}; do
    last=`jq ".[$n]|{date,link}" corona.json`
    date=`jq -rn "$last | .date"`
    link=`jq -rn "$last | .link"`

    wget $link -O archive/$date.html
done

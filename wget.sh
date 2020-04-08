#!/usr/bin/env bash

last=`jq '.[0]|{date,link}' corona.json`
date=`jq -rn "$last | .date"`
link=`jq -rn "$last | .link"`

wget $link -O archive/$date.html

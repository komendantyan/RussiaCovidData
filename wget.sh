#!/usr/bin/env bash

last=`jq '.[0]|{date,link}' corona.json`
date=`jq -rn "$last | .date"`
link=`jq -rn "$last | .link"`

wget $link -O archive/$date.html


last=`jq '.[0]|{date,link}' tests.json`
date=`jq -rn "$last | .date"`
link=`jq -rn "$last | .link"`

wget $link -O archive_info/$date.html

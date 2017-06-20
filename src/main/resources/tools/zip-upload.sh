#!/bin/sh
BASENAME=$(basename $0)
USAGE="${BASENAME} creates upload.zip from upload_info.json and all *.cvs in given directory.
Usage: ${BASENAME} fixture/directory"

complain()
{
  printf >&2 "%s\n" "$@"
  exit 1
}

[ $# -eq 1 ] || complain "$USAGE"
DIR=$(echo $1 | sed 's:/*$::')
[ -d $DIR ] || complain "$DIR doesn't seem to be a directory"
[ -f "$DIR/upload_info.json" ] || complain "Cannot find $DIR/upload_info.json"
csvs=$(find $DIR -maxdepth 1 -name \*.csv -print)
[ -n "$csvs" ] || complain "Cannot find any *.csv in $DIR"
exec zip -jD $DIR/upload.zip $DIR/upload_info.json $DIR/*.csv

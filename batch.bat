@ECHO OFF

call activate dn3

python daily_map.py

call conda deactivate

PAUSE



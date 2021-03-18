@ECHO OFF
ECHO Setting up Python environments...

conda env update -f environment3.yml
conda env list

PAUSE
EXIT

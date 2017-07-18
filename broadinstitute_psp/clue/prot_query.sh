### HOWTO:

# This is a thin wrapper to call the Python script prot_query.py on Clue. Its
# only input is the user-defined config file (YAML file) from the Query App.
# This config file provides several arguments, including the path to another
# config file (I know, sorry) that has additional parameters that are not
# controlled by the user (e.g. the cell lines in our corpus).

# 1. cd to the psp/broadinstitute_psp directory
# 2. Call this script.

#----------#

USER_INPUT_CONFIG_PATH=$1

# Activate conda environment
source activate psp

python clue/prot_query.py -u $USER_INPUT_CONFIG_PATH

# Deactivate conda environment
source deactivate
#!/usr/bin/bash

for i in {0..27}
do
command="qsub /pbs/home/t/tarmstro/Workspace/LST/template_builder/examples/generate_templates.sh $i"
eval $command
done

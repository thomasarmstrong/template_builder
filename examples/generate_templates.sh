#!/usr/bin/bash

export LD_LIBRARY_PATH=/opt/sge/lib/lx-amd64:/pbs/software/centos-7-x86_64/oracle/12.2.0/instantclient/lib::/usr/local/lib:/usr/local/oracle/product/instantclient:$LD_LIBRARY_PATH
export PATH=/opt/sge/bin/lx-amd64:/usr/afsws/bin:/opt/bin:/pbs/software/centos-7-x86_64/shift/prod/bin:/pbs/software/centos-7-x86_64/oracle/12.2.0/instantclient/bin:/usr/lib64/qt-3.3/bin:/opt/puppetlabs/bin:/opt/dell/srvadmin/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin:/usr/local/shared/bin:/pbs/home/t/tarmstro/bin:$PATH

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/pbs/home/t/tarmstro/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/pbs/home/t/tarmstro/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/pbs/home/t/tarmstro/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/pbs/home/t/tarmstro/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
conda activate cta-dev


export LOGFILE=/pbs/home/t/tarmstro/Workspace/LST/template_builder/examples/generate_templates_temp$1.log
command="python /pbs/home/t/tarmstro/Workspace/LST/template_builder/examples/generate_templates_cta.py -c /pbs/home/t/tarmstro/Workspace/LST/template_builder/examples/configs/cta_lapalma_lst_temp$1.yaml -o LST_LaPalms_temp_$1.templates.gz "
eval $command  1>>$LOGFILE 2>>$LOGFILE
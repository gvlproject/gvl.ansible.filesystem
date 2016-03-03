from galaxy.jobs import JobDestination
import os
import multiprocessing

# This rules file determines the number of local cpus and then sets the
# Slurm --ntasks parameter appropriately. The maximum and minimum cpus
# to use per job is listed below. These values can be altered to suit the
# current system. So for a 1 - 2 cpu system, the --ntasks is set to 1, for
# a 4 cpu system it is set to 2 and for 8 or above it is set to 4.

# Any other dynamic settings of cpu or other slurm parameters like walltime
# or memory can also be set here. An example is the mapping_dynamic_job_wrapper
# function. It looks at the size of the input files and determines the number
# of cpus to use. It could just as easily change the walltime or memory requirements.

MINCPUS = 1
MAXCPUS = 4

def _adjustcpus(x):
    if x < MINCPUS:
        return MINCPUS
    elif x > MAXCPUS:
        return MAXCPUS
    else:
        return x


def mapping_dynamic_job_wrapper(job):
    #allocate extra cpus for large files.
    cpus_avail = multiprocessing.cpu_count()
    inp_data = dict([(da.name, da.dataset) for da in job.input_datasets])
    inp_data.update([(da.name, da.dataset) for da in job.input_library_datasets])
    query_file = inp_data["fastq_input1"].file_name
    query_size = os.path.getsize(query_file)
    if query_size > 100 * 1024 * 1024:
        cpunum = cpus_avail
    else:
        cpunum = cpus_avail/2
    cpunum = _adjustcpus(cpunum)
    cpu_str = "--ntasks=" + str(cpunum)
    return JobDestination(runner="slurm", params={"nativeSpecification": cpu_str})


def default_dynamic_job_wrapper(job):
    #Allocate the number of cpus based on the number available (by instance size)
    cpus_avail = multiprocessing.cpu_count()
    cpunum = cpus_avail/2
    cpunum = _adjustcpus(cpunum)
    cpu_str = "--ntasks=" + str(cpunum)
    return JobDestination(runner="slurm", params={"nativeSpecification": cpu_str})

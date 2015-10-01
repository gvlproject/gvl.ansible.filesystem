#!/usr/bin/env python

import argparse
import logging
import time

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.client import ConnectionError
import datetime as dt
import yaml


# Omit (most of the) logging by external libraries
logging.getLogger('bioblend').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

DEFAULT_GALAXY_URL = "http://localhost:8080/"


class JobFailedException(Exception):
    pass


class ProgressConsoleHandler(logging.StreamHandler):

    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    on_same_line = False

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            same_line = hasattr(record, 'same_line')
            if self.on_same_line and not same_line:
                stream.write('\r\n')
            stream.write(msg)
            if same_line:
                stream.write('.')
                self.on_same_line = True
            else:
                stream.write('\r\n')
                self.on_same_line = False
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def load_indices_list(indices_file):
    """
    Load YAML from the `indices_file` and return a dict with the content.
    """
    with open(indices_file, 'r') as f:
        indices_list = yaml.load(f)
    return indices_list


def wait_for_data_manager_jobs(galaxy_ref, jobs):
    # Monitor the job(s)
    log.debug("\tJob running", extra={'same_line': True})
    for job in jobs:
        job_id = job.get('id')
        job_finished = False
        while not job_finished:
            job_state = galaxy_ref.jobs.show_job(job_id).get('state', '')
            if job_state == 'ok':
                job_finished = True
            elif job_state == 'error':
                raise JobFailedException("Job is in state error")
            log.debug("", extra={'same_line': True})
            time.sleep(10)


def run_data_manager(galaxy_ref, dbkey_name, dm_tool, tool_input):
    response = galaxy_ref.tools.run_tool('', dm_tool, tool_input)
    jobs = response.get('jobs', [])
    # Check if a job is actually running
    if len(jobs) == 0:
        raise JobFailedException("\t(!) No '{0}' job found for '{1}'".format(dm_tool,
                                                                             dbkey_name))
    else:
        wait_for_data_manager_jobs(galaxy_ref, jobs)


def install_genome(galaxy_ref, genome):
    """
    Runs all data managers provided to setup and install the specified genome.

    :type galaxy_ref: bioblend.galaxy.GalaxyInstance
    :param galaxy_ref: The Galaxy instance on which to install the genome

    :type genome: This is an individual dictionary element of the dbkeys array from the indices file
    :param genome: A dictionary containing information about an individual genome to install. Two attributes are
                treated specially: dbkey and data_managers. The dbkey is used as the identifier for a genome and
                the data_managers is a list of data_managers to run for this genome.
    """
    errored_dms = []
    dbkey_name = genome.get('dbkey')
    for idx, dm in enumerate(genome.get('data_managers')):
        dm_tool = dm.get('id')
        # Initate tool installation
        log.debug('[DM: {0}/{1}] Installing genome {2} with '
                  'Data Manager: {3}'.format(idx,
                                             len(genome.get('data_managers')), dbkey_name, dm_tool))
        tool_input = genome
        start = dt.datetime.now()
        try:
            run_data_manager(galaxy_ref, dbkey_name, dm_tool, tool_input)
            log.debug("\tDbkey '{0}' installed successfully in '{1}'".format(
                genome.get('dbkey'), dt.datetime.now() - start))
        except ConnectionError as e:
            response = None
            log.error("\t* Error installing genome {0} for DM {1} (after {2}): {3}"
                      .format(dbkey_name, dm_tool, dt.datetime.now() - start, e.body))
            errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
    return errored_dms


def install_genomes(galaxy_url, api_key, indices_file):
    istart = dt.datetime.now()
    galaxy_ref = GalaxyInstance(
        galaxy_url or indices_list['galaxy_instance'],
        api_key or indices_list['api_key'])
    indices_list = load_indices_list(indices_file)
    for idx, genome in enumerate(indices_list['genomes']):
        log.debug('Processing {0} of {1} genomes - name: {2}'.format(idx,
                                                                     len(indices_list['genomes']),
                                                                     genome['dbkey']))
        errored_dms = install_genome(galaxy_ref, genome)
    log.info("All genomes & DMs listed in '{0}' have been processed.".format(indices_file))
    log.info("Errored DMs: {0}".format(errored_dms))
    log.info("Total run time: {0}".format(dt.datetime.now() - istart))


def _setup_logging():
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s - %(message)s')
    progress = ProgressConsoleHandler()
    file_handler = logging.FileHandler('/tmp/galaxy_genome_install.log')
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(progress)
    logger.addHandler(file_handler)
    return logger

if __name__ == "__main__":
    global log
    log = _setup_logging()
    parser = argparse.ArgumentParser(description="usage: python %prog [options]")
    parser.add_argument(
        "-g",
        "--galaxy",
        default=DEFAULT_GALAXY_URL,
        help="URL of galaxy server to use. The default is %s" %
        DEFAULT_GALAXY_URL)
    parser.add_argument(
        "-a",
        "--api_key",
        type=str,
        help="Galaxy admin user API key",
        required=True)
    parser.add_argument(
        "-i",
        "--indices_file",
        type=str,
        help="Reference genomes to install (see genome_list.yaml.sample)",
        required=True)
    args = parser.parse_args()

    install_genomes(args.galaxy, args.api_key, args.indices_file)

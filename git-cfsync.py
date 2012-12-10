#!/usr/bin/env python3

import argparse
import logging
import os
import shlex
import subprocess
import sys

class CfGitRepository(object):
    '''A Git repository used for storing configuration files

    This class represents a git respository that is used to control
    configuration files and provides a set of actions useful for automating
    common tasks.

    Note: This object will run system commands, alter the environment and
    change directories.  Beware.
    '''
    def __init__(self, repopath):
        'Initialize the environment for running git commands'
        self.log = logging.getLogger('CfGitRepository')
        self.log.debug('Initialized logger')
        os.chdir(repopath)
        self._gather_sync_config()

    def _gather_sync_config(self):
        '''Read cfsync configuration for this repository

        cfsync configuration is stored via 'git-config', which makes it easy
        link configuration to particular repositories.  This procedure reads
        all known configuration values into self.config.
        '''
        config = {}
        for key in ('fetch', 'merge', 'pull'):
            try:
                config[key] = self._git('config --get-all cfsync.' + key)\
                                  .strip('\n').split('\n')
                self.log.debug('setting %s config to: %s', key, repr(config[key]))
            except subprocess.CalledProcessError:
                config[key] = None
        self.config = config

    def _git(self, cmdstr):
        cmd = ['git',] + shlex.split(cmdstr)
        self.log.debug("Running git command: %s", repr(cmd))
        return subprocess.check_output(cmd, universal_newlines=True)

    def _run_git_generic(self, subcmd_str):
        'Run a git command in a completely not-special way'
        for subcmd_target in self.config[subcmd_str]:
            self._git(subcmd_str + ' ' + subcmd_target)

    def run_periodic_tasks(self):
        'Perform tasks that should run periodically'
        for command in ('fetch', 'pull', 'merge'):
            if self.config[command]:
                self._run_git_generic(command)

def parse_arguments():
    'Parse arguments from command line invocation'
    parser = argparse.ArgumentParser(prog='git-cfsync')
    parser.add_argument('repopath', metavar='PATH',
                        help="path to git repository")
    parser.add_argument('-d', '--debug', action='store_const',
                        const=logging.DEBUG, dest='loglevel',
                        help="Enable debug messages")
    parser.add_argument('-v', '--verbose', action='store_const',
                        const=logging.INFO, dest='loglevel',
                        help="Enable verbose logging")
    parser.add_argument('-V', '--version', action='version', version='0.1')
    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.loglevel:
        logging.getLogger().setLevel(args.loglevel)
        logging.debug("Set logging level")

    try:
        cfgit = CfGitRepository(args.repopath)
        cfgit.run_periodic_tasks()
    except Exception as e:
        if args.loglevel == logging.DEBUG:
            raise e
        else:
            print('Error:', e, file=sys.stderr)

if __name__ == "__main__":
    main()

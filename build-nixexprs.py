#!/usr/bin/env python

import argparse
import contextlib
from datetime import datetime
from functools import partial
import logging
import os
import os.path as osp
import shutil
from subprocess import (
    check_call,
    check_output,
)
import sys
import tempfile


CHANNEL = 'bbp-nixpkgs-unstable'
CHANNELS_PATH = '/usr/share/nginx/html'
GIT_CLONE_PATH = '/tmp/nix-exprs'
NIX_EXPRS_GIT_URL = 'https://github.com/BlueBrain/bbp-nixpkgs.git'
NIX_EXPRS_GIT_BRANCH = None
BINARY_CACHE_URL = 'http://bbpnixcache.epfl.ch'
PATCHES_PATH = '/opt/src/nixexprs/patches'
LOGGER = logging.getLogger('nixexprs')
FNULL = open(os.devnull, 'w')
check_calls = [check_call]  # modified in daemon mode


@contextlib.contextmanager
def mkdtemp(**kwargs):
    """Create a temporary directory in a `with` context
    and remove it when leaving the context.
    """
    path = tempfile.mkdtemp(**kwargs)
    try:
        yield path
    finally:
        if osp.exists(path):
            shutil.rmtree(path)


@contextlib.contextmanager
def pushd(path):
    """Change CWD in a `with` context
    """
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)


def getopt():
    """Build options parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase verbosity level', default=0)
    parser.add_argument('--daemon', action='store_true')
    parser.add_argument('--channels-path', default=CHANNELS_PATH)
    parser.add_argument('--channel', default=CHANNEL)
    parser.add_argument('--git-clone-path', default=GIT_CLONE_PATH)
    parser.add_argument('--nix-exprs-git-url', default=NIX_EXPRS_GIT_URL)
    parser.add_argument('--nix-exprs-git-branch', default=NIX_EXPRS_GIT_BRANCH)
    parser.add_argument('--binary-cache-url', default=BINARY_CACHE_URL)
    return parser


def synchronize_nix_expressions(**kwargs):
    """Synchronize NIX expressions from remote
    """
    git_clone_path = kwargs.get('git_clone_path') or GIT_CLONE_PATH
    nix_exprs_git_url = kwargs.get('nix_exprs_git_url') or NIX_EXPRS_GIT_URL
    nix_exprs_git_branch = kwargs.get('nix_exprs_git_branch') or NIX_EXPRS_GIT_BRANCH
    patches_path = kwargs.get('patches_path') or PATCHES_PATH
    tarball_outdated = False
    if not osp.isdir(git_clone_path):
        LOGGER.info('Initial clone of repository %s', nix_exprs_git_url)
        check_calls[0](['git', 'clone', '--recursive',
                        nix_exprs_git_url, git_clone_path])
        with pushd(git_clone_path):
            if nix_exprs_git_branch is not None:
                check_calls[0](['git', 'checkout', nix_exprs_git_branch])
            for patch in os.listdir(patches_path):
                patch_file = osp.join(patches_path, patch)
                LOGGER.info('Applying patch: %s', patch_file)
                check_calls[0]('patch -p1 <' + patch_file,
                               shell=True)
        tarball_outdated = True
    else:
        with pushd(git_clone_path):
            check_calls[0](['git', 'remote', 'update'])
            local_rev = check_output(['git', 'rev-parse', '@']).strip()
            remote_rev = check_output(['git', 'rev-parse', '@{u}']).strip()
            if local_rev != remote_rev:
                LOGGER.warn('Git Remote changed.')
                tarball_outdated = True
            else:
                LOGGER.info('NIX expressions are up to date with remote')

    if tarball_outdated:
        update_nixexprs_tarball(**kwargs)
    return tarball_outdated


def update_nixexprs_tarball(**kwargs):
    git_clone_path = kwargs.get('git_clone_path') or GIT_CLONE_PATH
    binary_cache_url = kwargs.get('binary_cache_url') or BINARY_CACHE_URL
    channels_path = kwargs.get('channels_path') or CHANNELS_PATH
    channel = kwargs.get('channel') or CHANNEL
    binary_cache_file = osp.join(
        channels_path,
        'channels',
        channel,
        'binary-cache-url'
    )
    dist_archive = osp.join(
        channels_path,
        'channels',
        channel,
        'nixexprs.tar.bz2'
    )

    with pushd(git_clone_path):
        LOGGER.info('Pulling new changes')
        check_calls[0](['git', 'pull'])
        check_calls[0](['git', 'submodule', 'update',
                        '--recursive', '--init'])

    prefix = 'nixpkgs-' + datetime.now().strftime('%Y%m%d-%H%m%S') + '-'
    with mkdtemp(prefix=prefix) as path:
        os.rmdir(path)
        shutil.copytree(git_clone_path, path)
        with pushd(path):
            shutil.rmtree('.git')
            if osp.isfile('.gitmodules'):
                with open('.gitmodules') as istr:
                    for line in map(str.strip, istr.read().splitlines()):
                        if line.startswith('path'):
                            module = line.split('=', 1)[-1].lstrip()
                            module_git = osp.join(module, '.git')
                            if osp.isdir(module_git):
                                shutil.rmtree(module_git)
        with pushd(osp.dirname(path)):
            LOGGER.info('Compressing NIX expressions tarball')
            archive = osp.basename(path)
            check_calls[0](['tar', 'cf', archive + '.tar', archive])
            archive = archive + '.tar'
            check_calls[0](['bzip2', archive])
            archive = archive + '.bz2'
            if not osp.isdir(osp.dirname(dist_archive)):
                os.makedirs(osp.dirname(dist_archive))
            LOGGER.warn('Publishing new NIX expressions')
            shutil.move(archive, dist_archive)

    if not osp.isfile(binary_cache_file):
        with open(binary_cache_file, 'w') as ostr:
            ostr.write(binary_cache_url)
            ostr.write('\n')


def run_daemon(**kwargs):
    LOGGER.warn('Starting daemon')

    def write(s, out=sys.stdout):
        out.write(s)
        out.flush()
    while True:
        write('READY\n')
        LOGGER.debug('Waiting for event')
        line = sys.stdin.readline()
        headers = dict([x.split(':') for x in line.split()])
        LOGGER.debug('Received event header: %s', repr(headers))
        payload = sys.stdin.read(int(headers['len']))
        LOGGER.debug('Event payload: %s', repr(payload))
        try:
            synchronize_nix_expressions(**kwargs)
            write('RESULT 2\nOK')
        except Exception:
            LOGGER.exception('While updating NIX expressions')
            write('RESULT 4\nFAIL')


def main():
    parser = getopt()
    args = parser.parse_args()
    hdlr = logging.FileHandler('/var/log/nixexprs.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    LOGGER.addHandler(hdlr)
    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose > 1:
        level = logging.DEBUG
    LOGGER.setLevel(level)
    if args.daemon:
        check_calls[0] = partial(check_call, stdout=sys.stderr)
        run_daemon(**vars(args))
    else:
        synchronize_nix_expressions(**vars(args))


if __name__ == '__main__':
    main()

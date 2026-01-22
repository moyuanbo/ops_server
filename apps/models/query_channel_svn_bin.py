#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os

from apps.config import SVN_CONFIG

def channel_svn_bin(channel, rsync_mode):
    if channel == "lingjing_weixin" or channel == "weixin20":
        channel_svn_dir = os.path.join(SVN_CONFIG['svn_dir'], 'weixin')
    else:
        channel_svn_dir = os.path.join(SVN_CONFIG['svn_dir'], channel)

    if rsync_mode == 'update':
        package_file = os.path.join(str(channel_svn_dir), 'codeUpdate', 'bin.tar.gz')
    elif rsync_mode == 'reload':
        package_file = os.path.join(str(channel_svn_dir), 'hotUpdate', 'newfile.zip')
    elif rsync_mode == 'battle':
        package_file = os.path.join(str(channel_svn_dir), 'battleReportUpdate', 'tryOut.tar')
    else:
        package_file = None

    return package_file
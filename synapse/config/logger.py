# -*- coding: utf-8 -*-
# Copyright 2014, 2015 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ._base import Config
from synapse.util.logcontext import LoggingContextFilter
from twisted.python.log import PythonLoggingObserver
import logging
import logging.config
import yaml


class LoggingConfig(Config):
    def __init__(self, args):
        super(LoggingConfig, self).__init__(args)
        self.verbosity = int(args.verbose) if args.verbose else None
        self.log_config = self.abspath(args.log_config)
        self.log_file = self.abspath(args.log_file)
        self.access_log_file = self.abspath(args.access_log_file)

    @classmethod
    def add_arguments(cls, parser):
        super(LoggingConfig, cls).add_arguments(parser)
        logging_group = parser.add_argument_group("logging")
        logging_group.add_argument(
            '-v', '--verbose', dest="verbose", action='count',
            help="The verbosity level."
        )
        logging_group.add_argument(
            '-f', '--log-file', dest="log_file", default="homeserver.log",
            help="File to log to."
        )
        logging_group.add_argument(
            '--log-config', dest="log_config", default=None,
            help="Python logging config file"
        )
        logging_group.add_argument(
            '--access-log-file', dest="access_log_file", default="access.log",
            help="File to log server access to"
        )

    def setup_logging(self):
        log_format = (
            "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(request)s"
            " - %(message)s"
        )
        if self.log_config is None:

            level = logging.INFO
            level_for_storage = logging.INFO
            if self.verbosity:
                level = logging.DEBUG
                if self.verbosity > 1:
                    level_for_storage = logging.DEBUG

            # FIXME: we need a logging.WARN for a -q quiet option
            logger = logging.getLogger('')
            logger.setLevel(level)

            logging.getLogger('synapse.storage').setLevel(level_for_storage)

            formatter = logging.Formatter(log_format)
            if self.log_file:
                # TODO: Customisable file size / backup count
                handler = logging.handlers.RotatingFileHandler(
                    self.log_file, maxBytes=(1000 * 1000 * 100), backupCount=3
                )
            else:
                handler = logging.StreamHandler()
            handler.setFormatter(formatter)

            handler.addFilter(LoggingContextFilter(request=""))

            logger.addHandler(handler)

            if self.access_log_file:
                access_logger = logging.getLogger('synapse.access')
                # we log to both files by default
                access_logger.propagate = 1
                access_log_handler = logging.handlers.RotatingFileHandler(
                    self.access_log_file, maxBytes=(1000 * 1000 * 100), backupCount=3
                )
                access_log_formatter = logging.Formatter('%(message)s')
                access_log_handler.setFormatter(access_log_formatter)
                access_logger.addHandler(access_log_handler)
        else:
            with open(self.log_config, 'r') as f:
                logging.config.dictConfig(yaml.load(f))

        observer = PythonLoggingObserver()
        observer.start()

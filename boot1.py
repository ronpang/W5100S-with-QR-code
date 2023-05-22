# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
boot.py file for Pico data logging example. If this file is present when
the pico starts up, make the filesystem writeable by CircuitPython.
"""
import storage

storage.remount("/", readonly=False)

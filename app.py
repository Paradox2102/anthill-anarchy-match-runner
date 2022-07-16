#!/usr/bin/env python3

import config
import thread
import control
import overlay

if __name__ == '__main__':
    config.logger.info("Running")
    thread.cycle()
    config.socketio.run(config.app, host="0.0.0.0", port=80)
    config.logger.info("Done")
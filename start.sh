#!/bin/bash
export PYTHONPATH=$PYTHONPATH:./src
uvicorn legendary_potato.app.main:app --host 0.0.0.0 --port 8001 &
sleep infinity

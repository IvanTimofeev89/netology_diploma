#!/bin/bash
celery -A diploma_pj.celery worker -l info

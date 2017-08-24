#!/bin/bash

set -e
set -o pipefail

BORG_CMD="$HOME/bin/borg-linux64"
PATHS="$HOME/wip/ $HOME/.thunderbird/ $HOME/.mozilla/ $HOME/src"

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BORG_CMD=${BORG_CMD:-borg}
REPOSITORY=${REPOSITORY:-'pi@crashpi1:/media/data/borg'}
ARCHIVE_TAG=${ARCHIVE_TAG:-"$(whoami)@$(hostname -s)"}
TIMESTAMP_FORMAT=${TIMESTAMP_FORMAT:-"{now:%Y-%m-%d.%H%M%S}"}
ARCHIVE_NAME=${ARCHIVE_NAME:-"${ARCHIVE_TAG}_${TIMESTAMP_FORMAT}"}

DEFAULT_EXCLUDES="--exclude-caches --exclude '*/tmp/*' --exclude '*/nobackup/*' --exclude '*/no-backup/*' --exclude-if-present .nobackup --exclude-if-present .no-backup"
EXCLUDES=${EXCLUDES:-${DEFAULT_EXCLUDES} ${ADDITIONAL_EXCLUDES}}
. "$SRC_DIR/set_passphrase.sh"   # export BORG_PASSPHRASE="..."

export BORG_LOGGING_CONF=$HOME/.backpack/conf/borg-logging.conf

# if running interactively, add verbosity
[[ -t 1 ]] && VERBOSE=${VERBOSE:-"--progress --stats --info"}


CMD="${BORG_CMD} create --compression lz4 ${EXCLUDES} ${VERBOSE} ${ADDITIONAL_OPTIONS} ${REPOSITORY}::${ARCHIVE_NAME} ${PATHS}"
[[ -n "${VERBOSE}" ]] && echo "Running '$CMD'."
eval "$CMD" | tee ~/.backpack/log/latest-borg-run.log


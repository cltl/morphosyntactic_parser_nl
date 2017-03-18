set -e
DEST=${1:-$HOME/tools}
ALPINO_HOME="${DEST}/Alpino"
if [ -d "$ALPINO_HOME" ]; then
    echo "Found existing Alpino installation, remove that folder and re-run this script to reinstall"
    echo "ALPINO_HOME=$ALPINO_HOME"
    exit 1
fi

echo "Installing Alpino to $ALPINO_HOME"

mkdir -p $ALPINO_HOME
curl http://www.let.rug.nl/vannoord/alp/Alpino/versions/binary/latest.tar.gz | tar xz -C $DEST

echo "Successfully installed Alpino at:"
echo "ALPINO_HOME=$ALPINO_HOME"

export ALPINO_HOME

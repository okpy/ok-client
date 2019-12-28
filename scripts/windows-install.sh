target="./python-setup.exe"
curl -s -L -R -o "${target}" "https://www.python.org/ftp/python/${PYV}/python-${PYV}-amd64.exe"
"${target}" //quiet PrependPath=1 InstallAllUsers=1
rm -f -- "${target}"
python -m pip install -U pip
python -m pip install virtualenv
python -m virtualenv -p python env
source env/Scripts/activate
python -m pip install -r requirements.txt

brew install pyenv
py_full_version="${TRAVIS_PYTHON_VERSION}"
if [ -n "${py_full_version##*.*.*}" ]; then  # Do we have the full version number?
	pyenv install "${py_full_version}"
else
	git clone --depth=1 "https://github.com/momo-lab/xxenv-latest.git" "$(pyenv root)/plugins/xxenv-latest"
	pyenv install-latest "${py_full_version}"
fi
python"${py_full_version%%.*}" -m venv ~/venv
. ~/venv/bin/activate

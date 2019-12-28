urlbase="https://www.python.org/ftp/python/"
py_base_version="$1"
if [ -n "$[py_base_version}" ]; then
	py_base_version="$(printf "%s" "${TRAVIS_PYTHON_VERSION}" | sed 's/[][\\\.]/\\\0/g')"  # escape for sed
fi
py_full_version="$(curl -s -L --compressed "${urlbase}" | sed -n 's/.*<a href="\(${py_base_version}\(\.[0-9]\+\)*\)\/\?">.*/\1/p' | tail -n 1)"
if [ -n "${py_full_version}" ]; then
	arch_suffix=""
	if [ "${HOSTTYPE}" = "x86_64" ]; then
		arch_suffix="-amd64"
	fi
	targetdir="${SYSTEMROOT-.}\Python${py_full_version}"
	installer="${HOME}/python-installers/python-${py_full_version}${arch_suffix}.exe"
	mkdir -p -- "${installer##/**}"
	curl -s -L -R -o "${installer}" -- "${urlbase}${py_full_version}/${installer##*/}"
	MSYS2_ARG_CONV_EXCL="*" "${installer}" /quiet PrependPath=1 InstallAllUsers=1 TargetDir="${targetdir}"
	python="${targetdir}\python.exe"
	rm -f -- "${installer}"
	"${python}" -m venv env
	(
		. "env/Scripts/activate"
		python -m pip install -U pip
		python -m pip install -r requirements.txt
	)
else
	1>&2 echo "error: could not detect latest revision of Python ${TRAVIS_PYTHON_VERSION}"
fi

USERNAME=`cut ~/.local/share/unimi-dl/credentials.json -d '"' -f4`
PASSWORD=`cut ~/.local/share/unimi-dl/credentials.json -d '"' -f8`

test:
	USERNAME=$(USERNAME) PASSWORD=$(PASSWORD) python3 -m unittest unimi_dl/test/test_*.py
setup:
	ln -sf ~/.local/share/unimi-dl/credentials.json credentials.json

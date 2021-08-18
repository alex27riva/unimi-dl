from pathlib import Path
from json import dumps as json_dumps, load as json_load
from json.decoder import JSONDecodeError

class Credentials:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

class CredentialsManager:
    """
    Manages the `credentials` configuration file
    """
    def __init__(self, cred_path: str) -> None:
        self.path = Path(cred_path).expanduser()
        with(self.path.open("r") as credentials_file):
            credentials_dict = json_load(credentials_file)
            self.credentials = Credentials(credentials_dict["email"], credentials_dict["password"])

    def setCredentials(self, email: str, password: str):
        credentials = Credentials(email, password)
        self.credentials = credentials
        credentials.password = password

        with(self.path.open("w") as credentials_file):
            credentials_file.write(json_dumps(self.credentials))

    def getCredentials(self) -> Credentials:
        return self.credentials

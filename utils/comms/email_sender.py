import abc
import base64
import json
import logging
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class EmailSender(abc.ABC):

    @abc.abstractmethod
    def send(self, to: str, subject: str, message_text: str):
        pass

    def send_with_retries(self, to: str, subject: str, message_text: str, retries: int = 3):
        for i in range(retries):
            try:
                return self.send(to, subject, message_text)
            except HttpError as err:
                logging.warning(f"Error while sending message to {to}. "
                                f"Subject: {subject}. "
                                f"Error: {str(err)}. "
                                f"Attempt: {i}")
        return None


class MockSender(EmailSender):

    def send(self, to: str, subject: str, message_text: str):
        logging.info(f"Sending email to: {to}\n"
                     f"Subject: {subject}\n"
                     f"Text: {message_text}")
        return


class Gmail(EmailSender):
    _scopes = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.settings.sharing",
        "https://www.googleapis.com/auth/gmail.settings.basic",
    ]

    def __init__(self, token: str):
        self._token = token
        token_dict = json.loads(token)
        self._creds = Credentials.from_authorized_user_info(token_dict, self._scopes)
        self._service = build("gmail", "v1", credentials=self._creds)

    @classmethod
    def get_token_from_credentials(cls, credentials_path):
        """
        check this out: https://developers.google.com/gmail/api/quickstart/python?hl=ru
        credentials are created here: https://console.cloud.google.com/apis/credentials
        You create the credentials for the project, then save it as some credentials.json file
        and specify this path to the credentials_path variable.

        :return: a json with token that you pass later as a string to initialize the instance of a class
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, scopes=cls._scopes
        )
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        return creds.to_json()

    def get_send_as(self):
        return self._service.users().settings().sendAs().list(userId="me").execute()

    def send(self, to: str, subject: str, message_text: str):
        message = MIMEText(message_text, 'html')

        message["To"] = to
        message["Subject"] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            self._service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        return send_message

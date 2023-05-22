
import os
import requests
from dotenv import load_dotenv

load_dotenv()

domain = os.getenv("MAILGUN_DOMAIN")
api_key = os.getenv("MAILGUN_API_KEY")

def send_simple_message(to, subj, body):
    return requests.post(
		f"https://api.mailgun.net/v3/{domain}/messages",
		auth=("api", api_key),
		data={"from": f"Excited User <mailgun@{domain}>",
			"to": [to],
			"subject": subj,
			"text": body}
            )

def send_user_registration_message(email, username):
    return send_simple_message(
        email,
        "Successfully registered",
        f"Hello {username}, you have been successfully registered."
        )
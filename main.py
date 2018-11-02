import email, getpass, imaplib, os
import requests
import json
from time import sleep

from credentials import EMAIL, PASSWORD, HUB_KEY

detach_dir = '.'  # directory where to save attachments (default: current)
user = EMAIL
pwd = PASSWORD

bounce_str = ["Your message wasn't delivered", "There was a problem delivering your message",
              "couldn\'t be delivered", "Recipient address rejected", "Delivery has failed"]

# connecting to the gmail imap server
m = imaplib.IMAP4_SSL("imap.gmail.com")
m.login(user, pwd)
m.select('"Bounces"')

resp, items = m.search(None, "ALL")
items = items[0].split()

bounces = []

for emailid in items:
    resp, data = m.fetch(emailid, "(RFC822)")
    email_body = data[0][1]
    mail = email.message_from_bytes(email_body)

    if mail.get_content_maintype() != 'multipart':
        continue

    for part in mail.walk():

        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True)

            if body != '':
                bounces.append(body)

        if part.get('Content-Disposition') is None:
            continue

bounced_emails = []

while not bounces == []:
    try:
        bounce = bounces.pop().decode('ascii')
        found_bounce_text = False

        for bounce_value in bounce_str:
            if bounce_value in bounce:
                found_bounce_text = True

        if found_bounce_text and '@' in bounce:
            bounce_split = bounce.split(' ')
            contains_email = False
            while not bounce_split == [] or contains_email == True:
                new_check = bounce_split.pop()
                if '@' in new_check:
                    if '[' in new_check or ']' in new_check:
                        new_check = new_check[new_check.find("[") + 1:new_check.find("]")]
                    if '<' in new_check or '>' in new_check:
                        new_check = new_check[new_check.find("<") + 1:new_check.find(">")]
                    if '(' in new_check or ')' in new_check:
                        new_check = new_check[new_check.find("(") + 1:new_check.find(")")]
                    if '\r' in new_check:
                        new_check = new_check[0:new_check.find("\r")]
                    if '\n' in new_check:
                        new_check = new_check[0:new_check.find("\n")]
                    if ':' in new_check:
                        new_check = new_check[new_check.find(":") + 1:len(new_check)]
                    if '#' in new_check and ';' in new_check:
                        new_check = new_check[new_check.find("#") + 1:new_check.find(";")]
                    if '@' in new_check and not 'mail.gmail.com' in new_check and not 'sales-torch' in new_check and not 'spam' in new_check:
                        bounced_emails.append(new_check.rstrip('.').rstrip(';'))
                    contains_email = True

    except:
        print('Error')

bounced_emails = list(set(bounced_emails))
print(bounced_emails)
print('Bounced emails')
print(len(bounced_emails))


while not bounced_emails == []:
    to_remove = bounced_emails.pop()
    sleep(0.2)
    url = "https://api.hubapi.com/contacts/v1/contact/email/{}/profile?hapikey={}".format(to_remove, HUB_KEY)
    headers = {"content-type": "application/json"}
    r = requests.get(url)
    if r.status_code == 200:
        json_text = json.loads(r.text)
        vid = json_text['vid']
        print('Found ' + to_remove + ' in Hubspot.')
        r = requests.delete('https://api.hubapi.com/contacts/v1/contact/vid/{}?hapikey={}'.format(vid, HUB_KEY))
        if r.status_code == 200:
            print('Deleted {} from Hubspot!\n'.format(to_remove))
        else:
            print("Couldn't delete {} from Hubspot!\n".format(to_remove))
    else:
        print(to_remove + ' not in Hubspot.\n')

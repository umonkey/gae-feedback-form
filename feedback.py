# vim: set fileencoding=utf-8:

u"""A configurable feedback form for Google App Engine.

This script provides you with a feedback form that sends all messages to email.
Useful when your web site does not have this function (e.g. it's a static web
site).  For more details see the README.md file or the web site:

https://github.com/umonkey/gae-feedback-form
"""

import cgi
import urllib
import wsgiref.handlers

from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp


try:
    from config import RECAPTCHA_PUB, RECAPTCHA_PVT, ADMIN_EMAIL, SENDER_EMAIL
except ImportError:
    RECAPTCHA_PUB = RECAPTCHA_PVT = ADMIN_EMAIL = SENDER_EMAIL = None


RECAPTCHA_TEMPLATE = u"""<html><head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>Spam protection</title>
<style type="text/css">%(style)s</style>
</head><body id="spam">
<h1>Spam protection</h1>
<p>Please prove that you're not a robot.</p>
<form method="post">
<input type="hidden" name="from" value="%(from)s"/>
<input type="hidden" name="subject" value="%(subject)s"/>
<input type="hidden" name="message" value="%(message)s"/>
<input type="hidden" name="back" value="%(back)s"/>
<script type="text/javascript" src="http://www.google.com/recaptcha/api/challenge?k=%(recaptcha_pub)s"></script>
<button>Send the message</button>
</form>
</body>
</html>
"""


FORM_HTML = u'''
<html><head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>Feedback</title>
<style type="text/css">%(style)s</style>
</head><body id="form">
<form method="post">
%(form_fields)s
</form>
</body>
</html>'''

DEFAULT_STYLE_SHEET = u'''
body { margin: 10px; padding: 0; background-color: white; color: black; font: normal 10pt/14pt Ubuntu, sans-serif; }
div { margin-bottom: .5em; }
.text { display: block; width: 400px; }
textarea { height: 200px; }
#spam { width: 318px; margin: 100px auto auto; text-align: center }
'''


class RequestHandler(webapp.RequestHandler):
    def get(self):
        if "sent" in self.request.arguments():
            self.reply("Your message was sent.", content_type="text/plain")
            return

        recipient = self.request.get('to')
        subject = self.request.get('subject')
        sender = users.get_current_user() and users.get_current_user().email() or ''

        html = u''
        if 'sent' in self.request.arguments():
            html += u'<p id="sent">Your message was sent.</p>'
        html += u'<input type="hidden" name="back" value="%s"/>' % cgi.escape(self.request.get('back') or self.request.url + '?sent')
        html += u'<div id="sender"><label><span>Your address:</span><input type="text" class="text" name="from" value="%s"/></label></div>' % cgi.escape(sender)
        if subject:
            html += u'<input type="hidden" name="subject" value="%s"/>' % cgi.escape(subject)
        else:
            html += u'<div id="subject"><label><span>Subject:</span><input class="text" type="text" name="subject"/></label></div>'
        html += u'<div id="text"><label><span>Text:</span><textarea class="text" name="message"></textarea></label></div>'
        html += u'<div id="button"><input type="submit" value="Send message"/></div>'

        self.reply(FORM_HTML % {
            'style': DEFAULT_STYLE_SHEET or '',
            'form_fields': html,
        })

    def post(self):
        if self.check_recaptcha():
            return

        self.send_message(message=self.request.get("message"),
            back=self.request.get("back"),
            sender=self.request.get("from"),
            subject=self.request.get("subject"))

    def check_recaptcha(self):
        """Uses reCAPTCHA when possible.  Returns True if the request was
        handled and nothing else should be done.  False means normal processing
        should continue."""
        if RECAPTCHA_PVT is None:
            return False

        if "recaptcha_response_field" not in self.request.arguments():
            form = RECAPTCHA_TEMPLATE % {
                "from": cgi.escape(self.request.get("from")),
                "subject": cgi.escape(self.request.get("subject")),
                "message": cgi.escape(self.request.get("message")),
                "back": cgi.escape(self.request.get("back")),
                "style": DEFAULT_STYLE_SHEET,
                "recaptcha_pub": RECAPTCHA_PUB,
            }
            self.reply(form, content_type="text/html")
            return True

        check = self.fetch("http://www.google.com/recaptcha/api/verify", {
            "privatekey": RECAPTCHA_PVT,
            "remoteip": self.request.remote_addr,
            "challenge": self.request.get("recaptcha_challenge_field"),
            "response": self.request.get("recaptcha_response_field"),
        }).split("\n")

        if check[0] == 'true':
            return False  # False means OK, continue with the real form

        self.reply("Wrong answer.", content_type="text/plain")
        return True

    def send_message(self, message, back, sender, subject):
        if not sender:
            sender = "anonymous"
        if not subject:
            subject = "no subject"

        text = u'From: %s (%s)' % (sender, self.request.remote_addr)
        text += u'\n' + ('-' * len(text)) + '\n\n' + message

        mail.send_mail(sender=SENDER_EMAIL, to=ADMIN_EMAIL, subject=subject, body=text)
        self.redirect(self.request.get("back"))

    def reply(self, text, status=200, content_type='text/html'):
        self.response.set_status(status)
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(text.encode('utf-8'))

    def fetch(self, url, payload=None):
        method = urlfetch.GET
        if payload is not None:
            method = urlfetch.POST
            payload = urllib.urlencode(payload)
        result = urlfetch.fetch(url, payload=payload, method=method)
        return result.content


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        ('.*', RequestHandler),
    ]))

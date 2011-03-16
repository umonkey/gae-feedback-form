# vim: set fileencoding=utf-8:

u"""A configurable feedback form for Google App Engine.

This script provides you with a feedback form that sends all messages to email.
Useful when your web site does not have this function (e.g. it's a static web
site).  For more details see the README.md file or the web site:

https://github.com/umonkey/gae-feedback-form
"""

# Python imports.
import logging
import urllib
import wsgiref.handlers
from xml.sax.saxutils import escape as escape_attr

# GAE imports.
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

class FeedbackSettings(db.Model):
    From = db.StringProperty()
    ValidRecipients = db.StringListProperty()
    StyleSheet = db.TextProperty()
    ReCaptchaPublic = db.StringProperty()
    ReCaptchaPrivate = db.StringProperty()

SETTINGS_HTML = u'''
<html><head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>Feedback Settings</title>
<style type="text/css">%(style)s</style>
</head><body id="settings">
<h1><a href="%(home)s">Feedback</a> Settings</h1>
<form method="post">
<div><label>From: <input type="text" name="From" value="%(from)s" class="text"/></label></div>
<div><label>Valid recipients: <input type="text" name="ValidRecipients" value="%(valid)s" class="text"/></label></div>
<div><label><a href="https://www.google.com/recaptcha/admin/create">reCAPTCHA public key</a>: <input type="text" name="ReCaptchaPublic" value="%(rcpublic)s" class="text"/></label></div>
<div><label>reCAPTCHA private key: <input type="text" name="ReCaptchaPrivate" value="%(rcprivate)s" class="text"/></label></div>
<div><label>Custom style sheet:<textarea name="StyleSheet" class="text">%(style_text)s</textarea></label></div>
<input type="submit" value="Save"/>
</form>
</body>
</html>'''

FORM_HTML = u'''
<html><head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>Feedback Settings</title>
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
#settings textarea { white-space: nowrap; }
'''

class RequestHandler(webapp.RequestHandler):
    def get(self):
        if 'settings' in self.request.arguments():
            if not self.check_admin():
                return
            settings = self.load_settings()
            html = SETTINGS_HTML % {
                'style': settings.StyleSheet or '',
                'style_text': settings.StyleSheet or '',
                'home': self.request.path,
                'from': settings.From or '',
                'valid': settings.ValidRecipients and u', '.join(settings.ValidRecipients) or '',
                'rcpublic': settings.ReCaptchaPublic or '',
                'rcprivate': settings.ReCaptchaPrivate or '',
            }
            return self.reply(html)

        else:
            settings = self.load_settings()
            recipient = self.request.get('to') or settings.ValidRecipients[0]
            subject = self.request.get('subject')
            sender = users.get_current_user() and users.get_current_user().email() or ''

            html = u''
            if 'sent' in self.request.arguments():
                html += u'<p id="sent">Your message was sent.</p>'
            html += u'<input type="hidden" name="back" value="%s"/>' % escape_attr(self.request.get('back') or self.request.url + '?sent')
            html += u'<div id="sender"><label><span>Your address:</span><input type="text" class="text" name="from" value="%s"/></label></div>' % escape_attr(sender)
            if subject:
                html += u'<input type="hidden" name="subject" value="%s"/>' % escape_attr(subject)
            else:
                html += u'<div id="subject"><label><span>Subject:</span><input class="text" type="text" name="subject"/></label></div>'
            html += u'<div id="text"><label><span>Text:</span><textarea class="text" name="message"></textarea></label></div>'
            html += u'<script type="text/javascript" src="http://www.google.com/recaptcha/api/challenge?k=%s"></script>' % settings.ReCaptchaPublic
            html += u'<div id="button"><input type="submit" value="Send message"/></div>'

            self.reply(FORM_HTML % {
                'style': settings.StyleSheet or '',
                'form_fields': html,
            })

    def post(self):
        if 'settings' in self.request.arguments():
            if not self.check_admin():
                return
            settings = self.load_settings()
            for field in settings.fields():
                value = self.request.get(field)
                if field == 'ValidRecipients':
                    value = [x.strip() for x in value.split(',') if x.strip()]
                setattr(settings, field, value)
            settings.put()
            self.redirect(self.request.url)

        elif False: # debug
            output = dict([(arg, self.request.get(arg)) for arg in self.request.arguments()])
            self.reply(unicode(output), content_type='text/plain')

        else:
            settings = self.load_settings()
            if not self.check_captcha(settings):
                return

            sender = self.request.get('from') or 'anonymous'
            message = self.request.get('message') or 'no message'
            back = self.request.get('back') or self.request.path

            subject = self.request.get('subject').strip() or 'no subject'
            subject_prefix = self.request.get('prefix')
            if subject_prefix:
                subject = subject_prefix.strip() + ' ' + subject

            recipient = self.request.get('to')
            if not recipient or recipient not in settings.ValidRecipients:
                recipient = settings.ValidRecipients[0]

            text = u'From: %s' % sender
            text += u'\n' + ('-' * len(text)) + '\n\n' + message

            mail.send_mail(sender=sender, to=recipient, subject=subject, body=text)
            self.redirect(self.request.get('back'))

    def check_admin(self):
        """Checks whether the user is an admin.
        
        Forces anonymous users to log in, shows an error to non-admins."""
        if users.get_current_user() is None:
            self.redirect(users.create_login_url(self.request.url))
            return False
        if not users.is_current_user_admin():
            self.reply('<html><body><h1>Access denied</h1><p>Only admins are allowed to use this page.</p></body></html>', status=403)
            return False
        return True

    def check_captcha(self, settings):
        if not settings.ReCaptchaPublic or not settings.ReCaptchaPrivate:
            return True
        check = self.fetch('http://www.google.com/recaptcha/api/verify', {
            'privatekey': settings.ReCaptchaPrivate,
            'remoteip': self.request.remote_addr,
            'challenge': self.request.get('recaptcha_challenge_field'),
            'response': self.request.get('recaptcha_response_field'),
        }).split('\n')
        if check[0] == 'true':
            return True
        self.reply('Wrong answer.', content_type='text/plain')
        return False

    def reply(self, text, status=200, content_type='text/html'):
        self.response.set_status(status)
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(text.encode('utf-8'))

    def load_settings(self):
        settings = FeedbackSettings.all().get()
        if settings is None:
            settings = FeedbackSettings(StyleSheet=DEFAULT_STYLE_SHEET,
                ValidRecipients=['info@example.com'])
        return settings

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

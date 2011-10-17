GAE Feedback form handler
=========================

This script provides you with a feedback form that sends all messages to email.
Useful when your web site does not have this function (e.g. it's a static web
site).

Written by Justin Forest (hex@umonkey.net) in 2011.

License: BSD.


Installation
------------

To use this script add it as a handler to whatever path you want by adding this
to your app.yaml:

    handlers:
    - url: /mail
      script: feedback.py


Configuration
-------------

The script reads configuration from a file named config.py, from which the
following variables are used:

- ADMIN_EMAIL -- this is where the messages will be sent.
- SENDER_EMAIL -- this is from whose name they'll be sent.
- RECAPTCHA_PUB, RECAPTCHA_PVT -- keys for [using reCAPTCHA][re] (not used if
  the keys are not defined).



How to use it
-------------

Install the script and access it using your web browser.  If you can
successfully receive messages, you can either link to the built-in form from
your web site, or use a customized form.  The following fields are used:

- subject -- a subject line,
- message -- tye main text,
- sender -- an email address (will be included in the body),
- back -- where to send the user to after sending the message.

You can use hidden fields for all, it's OK.



Known bugs
----------

- reCAPTCHA only works with JavaScript.
- Form fields and messages are not localized.

If you find more bugs, email me at hex@umonkey.net.  You can email me with this
script from my web site at:

http://umonkey.net/mail/

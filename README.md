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
    - url: /feedback
      script: feedback.py


Configuration
-------------

The script lets you customize the sender address, available recipients (so that
it's not used to spam people), use custom CSS and reCAPTCHA.  These things are
configured in the settings page which can be accessed by application admins by
adding the "?settings" suffix to the web page, e.g.:

    /feedback?settings



How to use it
-------------

First you need to install this script and make sure it works by sending a
message to yourself.  When that works, embed the form in your web site using an
iframe, like this:

    <iframe src="https://app-name.appspot.com/feedback"></iframe>

You can set predefined subject and recipient by adding the "to" and "subject"
arguments to the form URL.  Also, the "back" argument is where the user is
redirected after the message is successfully sent.  Example:

    .../feedback?to=info@example.com&back=http://example.com/mail-sent.html



Known bugs
----------

- reCAPTCHA only works with JavaScript.
- If you fail to guess captcha, an plain text error message is shown (this can
  be fixed by using AJAX or otherwise).

If you find more bugs, email me at hex@umonkey.net.

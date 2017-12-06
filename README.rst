bcsio
=====

An asynchronous `Bascamp API <https://github.com/basecamp/bc3-api>`_ library.

This is heavily cargo-culted from `gidgethub <https://gidgethub.readthedocs.io/en/stable/>_`


Auth
----

To connect to basecamp you need to register an 'application' at
https://launchpad.37signals.com/integrations.  Use any URL when it asks.  You should
get a 'key' and a 'secret'.

Once that is done, get a token by ::

  import webbrowser
  consumer_key = 'XXX'
  redirect_url = 'https://NNNNNN'
  url = f'https://launchpad.37signals.com/authorization/new?type=web_server&client_id={consumer_key}&redirect_uri={redirect_url}'
  webbrowser.open(url)

This will then go through basecamp's log in and ask if you would like
to allow your application to access your basecamp account.  When this
is done it will dump you back the URL you have it above with a 8
character hex string.  Use this to get your token ::

  import requests
  consumer_secret = 'XXXXX'
  vc = 'deadbeef'
  ret = requests.post(f'https://launchpad.37signals.com/authorization/token?type=web_server&client_id={consumer_key}&redirect_uri={redirect_url}&client_secret={consumer_secret}&code={vc}')
  token = ret.json()


Treat the *consumer_key*, *consumer_secret*, and *token* as you would a password.

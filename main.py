from flask import Flask, redirect, url_for, session, request,send_file,render_template
from flask_oauthlib.client import OAuth, OAuthException
from PIL import Image
from io import BytesIO
import facebook as fb
import sys
import logging
import os
import requests
import base64

FACEBOOK_APP_ID = os.environ['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = os.environ['FACEBOOK_APP_SECRET']


app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

facebook = oauth.remote_app(
    'facebook',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)

def manipulate(url):
    i = Image.open(BytesIO(url.content))
    nn = Image.open('netneutrality.png')
    ii = i.copy()
    width,height = ii.size
    ii.paste(nn,(width-200,height-200),nn)
    byte_io = BytesIO()
    ii.save(byte_io, 'PNG')
    return send_file(byte_io, mimetype='image/png',attachment_filename="nnprofilepic.png",as_attachment=True),ii

@app.route('/')
def index():
    if 'oauth_token' in session:
        graph = fb.GraphAPI(access_token=session['oauth_token'][0], version='2.5')
        print(session['oauth_token'][0])
        profile_img = graph.get_object('me/picture?width=9999&redirect=false')['data']['url']
        name = graph.get_object('me')['name']
        r = requests.get(profile_img)
        ii = manipulate(r)[1]
        imgserve = BytesIO()
        ii.save(imgserve, 'PNG')
        imgserve.seek(0)
        img_tag = base64.b64encode(imgserve.getvalue()).decode()
        return render_template('result.html',imgsrc=img_tag,name = name ,url = r.url[8:])

    else:
        return render_template('index.html')


@app.route('/connect')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


@app.route('/login/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'],'')
    return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    app.run()

from flask import current_app, render_template, url_for
from flask_mail import Mail, Message
from threading import Thread

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipient, template, **kwargs):
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    if not sender:
        raise ValueError("Email configuration is incomplete. Please set MAIL_USERNAME or MAIL_DEFAULT_SENDER in .env file")
    
    msg = Message(subject, 
                 sender=sender,
                 recipients=[recipient])
    msg.html = render_template(template, **kwargs)
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

def send_verification_email(user, token):
    # Get the host from the request context or use a default
    if current_app.config['ENV'] == 'development':
        host = '127.0.0.1:5000'
        scheme = 'http'
    else:
        host = 'bursary-app.onrender.com'
        scheme = 'https'  # Always use HTTPS for production

    # Remove the _host parameter if it's the production domain
    verification_url = url_for('auth.verify_email',
                             token=token,
                             _external=True,
                             _scheme=scheme)
    
    # Remove any unwanted query parameters
    if '?_host=' in verification_url:
        verification_url = verification_url.split('?_host=')[0]
    
    send_email('Verify Your Email - Bursary Application System',
              recipient=user.email,
              template='auth/email/verify_email.html',
              user=user,
              verification_url=verification_url)

def send_password_reset_email(user, token):
    # Get the host from the request context or use a default
    if current_app.config['ENV'] == 'development':
        host = '127.0.0.1:5000'
        scheme = 'http'
    else:
        host = 'bursary-app.onrender.com'
        scheme = 'https'  # Always use HTTPS for production

    reset_url = url_for('auth.reset_password',
                       token=token,
                       _external=True,
                       _scheme=scheme)
    
    # Remove any unwanted query parameters
    if '?_host=' in reset_url:
        reset_url = reset_url.split('?_host=')[0]
    
    send_email('Reset Your Password - Bursary Application System',
              recipient=user.email,
              template='auth/email/reset_password.html',
              user=user,
              reset_url=reset_url)

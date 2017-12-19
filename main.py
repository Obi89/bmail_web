#!/usr/bin/env python
import os
import jinja2
import webapp2
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import urlfetch
import json
import urllib


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        user = users.get_current_user()
        params["user"] = user

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            params["logout_url"] = logout_url
        else:
            logged_in = False
            login_url = users.create_login_url('/boogle')
            params["login_url"] = login_url

        params["logged_in"] = logged_in

        template = jinja_env.get_template(view_filename)

        return self.response.out.write(template.render(params))

class Message(ndb.Model):
    send = ndb.StringProperty()
    email = ndb.StringProperty()
    subject = ndb.StringProperty()
    message = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    deleted = ndb.BooleanProperty(default=False)

class Contact(ndb.Model):
    c_user = ndb.StringProperty()
    c_name = ndb.StringProperty()
    c_email = ndb.StringProperty()
    c_mobil = ndb.StringProperty()
    c_date = ndb.TextProperty()
    c_address = ndb.TextProperty()
    c_deleted = ndb.BooleanProperty(default=False)

class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("main.html")


class Boogle(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()

        params = {"messages": messages}
        return self.render_template("boogle.html", params=params)

    def post(self):
        user = users.get_current_user()

        if not user:

            return self.write("You are not logged in!")

        send = self.request.get("send")
        email = self.request.get("email")
        subject = self.request.get("subject")
        message = self.request.get("message")

        if not email:
            return self.write("Please enter a e-mail!")

        if "<script>" in message:
            return self.write("Can't hack me!")


        msg_object = Message(send=send, email=email, subject=subject,  message=message.replace("<script>", ""))
        msg_object.put()
        messages = Message.query(Message.deleted == False).fetch()
        params = {"messages": messages}


        return self.redirect_to("boogle-site", params=params)

class ContactHandler(BaseHandler):
    def get(self):
        contacts = Contact.query(Contact.c_deleted == False).fetch()

        params = {"contacts": contacts}
        return self.render_template("contact.html", params=params)

    def post(self):
        user = users.get_current_user()

        if not user:

            return self.write("You are not logged in!")

        c_user = self.request.get("c_user")
        c_name = self.request.get("c_name")
        c_email = self.request.get("c_email")
        c_mobil = self.request.get("c_mobil")
        c_date = self.request.get("c_date")
        c_address = self.request.get("c_address")

        msg_object = Contact(c_user=c_user, c_name=c_name, c_email=c_email, c_mobil=c_mobil, c_date=c_date, c_address=c_address)
        msg_object.put()
        contacts = Contact.query(Contact.c_deleted == False).fetch()
        params = {"contacts": contacts}


        return self.redirect_to("contact-site", params=params)

class ContactDelete(BaseHandler):
    def get(self, contact_id):
        contact = Contact.get_by_id(int(contact_id))

        params = {"contact": contact}

        return self.render_template("contact_delete.html", params=params)

    def post(self, contact_id):
        contact = Contact.get_by_id(int(contact_id))

        contact.deleted = True
        contact.put()

        return self.redirect_to("contact-site")


class Inbox(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()

        params = {"messages": messages}

        return self.render_template("inbox.html", params=params)


class Outbox(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()

        params = {"messages": messages}

        return self.render_template("outbox.html", params=params)


class MessageShow(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_show.html", params=params)



class MessageDelete(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_delete.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.deleted = True
        message.put()

        return self.redirect_to("boogle-site")


class MessagesDeleted(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == True).fetch()

        params = {"messages": messages}

        return self.render_template("deleted_messages.html", params=params)


class MessageRestore(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_restore.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.deleted = False
        message.put()

        return self.redirect_to("boogle-site")


class MessageCompleteDeleted(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_delete_complete.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.key.delete()

        return self.redirect_to("deleted-messages")


class Weather(BaseHandler):
    def get(self):
        url = "http://api.openweathermap.org/data/2.5/weather?q=Vienna,at&units=metric&appid=6aa9181f8379ea03bdb74008ab5aa247"
        result = urlfetch.fetch(url)

        weather_info = json.loads(result.content)
        params = {"weather_info": weather_info}
        self.render_template("weather.html", params)

    def post(self):

        city = self.request.get("city")

        url = "http://api.openweathermap.org/data/2.5/weather?" + str(city) + "&units=metric&appid=6aa9181f8379ea03bdb74008ab5aa247"
        result = urlfetch.fetch(url)
        weather_info = json.loads(result.content)

        params = {"weather_info": weather_info}
        self.render_template("weather.html", params)



app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/boogle', Boogle, name="boogle-site"),
    webapp2.Route('/inbox', Inbox, name="inbox-site"),
    webapp2.Route('/outbox', Outbox, name="outbox-site"),
    webapp2.Route('/message/<message_id:\d+>/show', MessageShow, name="message-show"),
    webapp2.Route('/message/<message_id:\d+>/delete', MessageDelete, name="message-delete"),
    webapp2.Route('/message/<message_id:\d+>/restore', MessageRestore, name="message-restore"),
    webapp2.Route('/message/<message_id:\d+>/complete-delete', MessageCompleteDeleted, name="message-delete-complete"),
    webapp2.Route('/deleted', MessagesDeleted, name="deleted-messages"),
    webapp2.Route('/contact', ContactHandler, name="contact-site"),
    webapp2.Route('/contact/<contact_id:\d+>/delete', ContactDelete, name="contact-delete"),
    webapp2.Route('/weather', Weather, name="weather-site"),
], debug=True)
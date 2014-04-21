'''
Created on 2014-4-18

@author: vedopar
'''
import os
import webapp2,json
import urllib,urllib2,re
import cookielib

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

def google_search2(req):
    url='https://ajax.googleapis.com/ajax/services/search/images'+'?v=1.0&rsz=8&q='+req
    #url = ('https://ajax.googleapis.com/ajax/services/search/images?' +'v=1.0&q=barack%20obama&userip=INSERT-USER-IP')

    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    json_acceptable_string = response.read().replace("'", "\"")
    d = json.loads(json_acceptable_string)
    res=""
    for r in d['responseData']['results']:
        res=res+r['titleNoFormatting'].encode('utf-8')+' '
        res=res+r['contentNoFormatting'].encode('utf-8')+'\n'
    return res
        
        
class MainHandler(webapp2.RequestHandler):
    def get(self):
        for key in blobstore.BlobInfo.all().run():
            key.delete()
        upload_url = blobstore.create_upload_url('/upload')
        #google_search()
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" name="submit" value="Submit"> </form></body></html>""")

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.redirect('/serve/%s' % blob_info.key())

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        #self.send_blob(blob_info)
        url= images.get_serving_url(blob_info.key())
        self.response.out.write("<html><body><p>"+url+"</p>")
        self.response.out.write(google_search2(url))
        self.response.out.write("</p></body></html>")

application = webapp2.WSGIApplication([('/', MainHandler),
                               ('/upload', UploadHandler),
                               ('/serve/([^/]+)?', ServeHandler)],
                              debug=True)
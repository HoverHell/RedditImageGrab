from collections import namedtuple


class gfycat(object):

    """
    A very simple module that allows you to
    1. upload a gif to gfycat from a remote location
    2. upload a gif to gfycat from local machine
    3. query the upload url
    4. query an existing gfycat link
    5. query if a link is already exist
    6. download the mp4 file
    """

    # Urls
    url = "http://gfycat.com"
    upload_url = "http://upload.gfycat.com"
    post_url = 'https://gifaffe.s3.amazonaws.com/'
    get_url = "http://upload.gfycat.com/transcode/"

    def __init__(self):
        super(gfycat, self).__init__()

    def __fetch(self, url, param):
        import urllib2
        import json
        try:
            # added simple User-Ajent string to avoid CloudFlare block this request
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib2.Request(url+param, None, headers)
            connection = urllib2.urlopen(req).read()
        except urllib2.HTTPError, err:
            raise ValueError(err.read())
        result = namedtuple("result", "raw json")
        return result(raw=connection, json=json.loads(connection))

    def upload(self, param):
        import random
        import string
        # gfycat needs to get a random string before our search parameter
        randomString = ''.join(random.choice
            (string.ascii_uppercase + string.digits) for _ in range(5))
        result = self.__fetch(self.upload_url,
            "/transcode/%s?fetchUrl=%s" % (randomString, param))
        if "error" in result.json:
            raise ValueError("%s" % result.json["error"])
        return _gfycatUpload(result)

    def uploadFile(self, file):
        result = self.__fileHandler(file)
        if "error" in result.json:
            raise ValueError("%s" % result.json["error"])
        return _gfycatUpload(result)

    def __fileHandler(self, file):
        # Thanks thesourabh for the implementation
        import random
        import string
        import requests
        # gfycat needs a random key before upload
        key = ''.join(random.choice
            (string.ascii_uppercase + string.digits) for _ in range(10))
        # gfycat form data
        form = [('key', key)]
        form.append(('acl', 'private'))
        form.append(('AWSAccessKeyId', 'AKIAIT4VU4B7G2LQYKZQ'))
        form.append(('success_action_status', '200'))
        form.append(('signature', 'mk9t/U/wRN4/uU01mXfeTe2Kcoc='))
        form.append(('Content-Type', 'image/gif'))
        form.append(('policy', 'eyAiZXhwaXJhdGlvbiI6ICIyMDIwLTEyLTAxVDEyOjAwOjAwLjAwMFoiLAogICAgICAgICAgICAiY29uZGl0aW9ucyI6IFsKICAgICAgICAgICAgeyJidWNrZXQiOiAiZ2lmYWZmZSJ9LAogICAgICAgICAgICBbInN0YXJ0cy13aXRoIiwgIiRrZXkiLCAiIl0sCiAgICAgICAgICAgIHsiYWNsIjogInByaXZhdGUifSwKCSAgICB7InN1Y2Nlc3NfYWN0aW9uX3N0YXR1cyI6ICIyMDAifSwKICAgICAgICAgICAgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgIiJdLAogICAgICAgICAgICBbImNvbnRlbnQtbGVuZ3RoLXJhbmdlIiwgMCwgNTI0Mjg4MDAwXQogICAgICAgICAgICBdCiAgICAgICAgICB9'))
        with open(file, 'rb') as upfile:
            form.append(('file', upfile))
            req = requests.post(self.post_url, files=form)
        if (int(req.status_code) != 200):
            raise ValueError("Error uploading the file: %s" % req.status_code)
        req = requests.get(self.get_url+key)
        result = namedtuple("result", "raw json")
        return result(raw=req, json=req.json())

    def more(self, param):
        result = self.__fetch(self.url, "/cajax/get/%s" % param)
        if "error" in result.json["gfyItem"]:
            raise ValueError("%s" % self.json["gfyItem"]["error"])
        return _gfycatMore(result)

    def check(self, param):
        res = self.__fetch(self.url, "/cajax/checkUrl/%s" % param)
        if "error" in res.json:
            raise ValueError("%s" % self.json["error"])
        return _gfycatCheck(res)


class _gfycatUtils(object):

    """
    A utility class that provides the necessary common
    for all the other classes
    """

    def __init__(self, param, json):
        super(_gfycatUtils, self).__init__()
        # This can be used for other functions related to this class
        self.res = param
        self.js = json

    def raw(self):
        return self.res.raw

    def json(self):
        return self.js

    def get(self, what):
        try:
            return self.js[what]
        except KeyError as error:
            return ("Sorry, can't find %s" % error)

    def download(self, location):
        import urllib2
        if not location.endswith(".mp4"):
            location = location + self.get("gfyName") + ".mp4"
        try:
            # added simple User-Ajent string to avoid CloudFlare block this request
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib2.Request(self.get("mp4Url"), None, headers)
            file = urllib2.urlopen(req)
            # make sure that the status code is 200, and the content type is mp4
            if int(file.code) is not 200 or file.headers["content-type"] != "video/mp4":
                raise ValueError("Problem downlading the file. Status code is %s or the content-type is not right %s"
                    % (file.code, file.headers["content-type"]))
            data = file.read()
            with open(location, "wb") as mp4:
                mp4.write(data)
        except urllib2.HTTPError, err:
            raise ValueError(err.read())

    def formated(self, ignoreNull=False):
            import json
            if not ignoreNull:
                return json.dumps(self.js, indent=4,
                    separators=(',', ': ')).strip('{}\n')
            else:
                raise NotImplementedError


class _gfycatUpload(_gfycatUtils):

    """
    The upload class, this will be used for uploading files
    from a remote server
    """

    def __init__(self, param):
        super(_gfycatUpload, self).__init__(param, param.json)


class _gfycatMore(_gfycatUtils):

    """
    This class will provide more information for an existing url
    """

    def __init__(self, param):
        super(_gfycatMore, self).__init__(param, param.json["gfyItem"])


class _gfycatCheck(_gfycatUtils):

    """
    This call will allow to query if a link is already known
    """

    def __init__(self, param):
        super(_gfycatCheck, self).__init__(param, param.json)

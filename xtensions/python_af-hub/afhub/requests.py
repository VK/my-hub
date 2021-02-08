import os.path as _path
import requests as _requests

class Requests:

    def __init__(self, config_section):
        r"""
        Encapsulate standard python requests with af-hub config
        :param config_section: name of the config secion to read params.

        Example /defaults.cfg:
        ======================
        [serverA]
        url = https://???/
        user = ???
        pass = ???

        [serverB]
        url = https://???/
        token = ???
        """
        import configparser

        config = configparser.ConfigParser()
        config.read('/defaults.cfg')

        if not config.has_section(config_section):
            raise Exception(f"Config section {config_section} is missing")

        self.__url = config[config_section]["url"]

        if "token" in config[config_section]:
            self.__auth = "bearer"
            self.__token = config[config_section]["token"]

        if "user" in config[config_section]:
            self.__auth = "basic"
            self.__user = config[config_section]["user"]
            self.__password = config[config_section]["pass"]

    def __get_url(self, url):
        if "http" in url:
            return url
        else:
            return _path.join(self.__url, url)

    def __add_auth(self, args):
        """
        add authentification to typical requests
        """
        if self.__auth == "bearer":
            if "header" not in args:
                args["header"] = {}
            args["header"]["Authorization"] = f"Bearer {self.__token}"
        if self.__auth == "basic":
            args["auth"] = (self.__user, self.__password)
        return args

    def get(self, url, **kwargs):
        r"""Sends a GET request.

        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.get(self.__get_url(url), self.__add_auth(kwargs))


    def options(self, url, **kwargs):
        r"""Sends a GET request.

        :param url: URL for the new :class:`Request` object.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.options(self.__get_url(url), self.__add_auth(kwargs))


    def head(self, url, **kwargs):
        r"""Sends a GET request.

        :param url: URL for the new :class:`Request` object.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.head(self.__get_url(url), self.__add_auth(kwargs))        

    
    def post(self, url, **kwargs):
        r"""Sends a POST request.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.post(self.__get_url(url), self.__add_auth(kwargs))


    def put(self, url, **kwargs):
        r"""Sends a PUT request.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.put(self.__get_url(url), self.__add_auth(kwargs))


    def patch(self, url, **kwargs):
        r"""Sends a PATCH request.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.patch(self.__get_url(url), self.__add_auth(kwargs))


    def delete(self, url, **kwargs):
        r"""Sends a DELETE request.

        :param url: URL for the new :class:`Request` object.
        :param **kwargs: Optional arguments that `request` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        return _requests.delete(self.__get_url(url), self.__add_auth(kwargs))



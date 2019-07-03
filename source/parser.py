from requests.exceptions import ConnectionError
from random import choice
import requests_html as rh

class BaseParser(object):
    """Parrent Class for Parser"""
    def __init__(self):
        self.session = rh.HTMLSession()


    def simple_parse(self, url, selector_dict):
        """
        Method for parse a tags
        input:
            1. url of the page
            2. dictionary like {'title': {'selector': 'div.menu', 'single':True, 'parse': 'link'},
                                'article': {'selector':'div.article', 'single':False, 'parse': 'text'}, e.t.c}
        output - dictionary like:
            {'title': 'https://www.sciencedirect.com', 'article': ['Usage of primat psycholohy', 'Healthy and nocallories food'}
        """
        self.current_url = url
        self.selector_dict = selector_dict
        self.html_page = self._get_request()

        if type(self.html_page) is str:
            return "Lose connection or invalid url"

        self.parse_result = self._find_selectors()

        return self.parse_result

    def _get_request(self):
        """
        Method for get request
        """
        try:
            return self.session.get(self.current_url).html
        except ConnectionError:
            return "Connecton failed"

    def _find_selectors(self):
        """
        Method for searching tags on the page
        If element exist retur
        """
        self.find_result = {}

        for self.entity in self.selector_dict:
            self.selector = self.selector_dict[self.entity]['selector']
            self.is_single = self.selector_dict[self.entity]['single']
            self.result_elements = self.html_page.find(self.selector, first=self.is_single)
            if self.result_elements:
                self.find_result[self.entity] = self._find_in_elements()
            else:
                self.find_result[self.entity] = None

        return self.find_result

    def _find_in_elements(self):
        """
        function for find in elements. If element is single - use self._find_in_element,
        If not single - use "for" loop and return list of results
        """
        if self.is_single:
            self.result_element = self.result_elements
            return self._find_in_element()
        # if not single
        self.result_for_elements = []  # output list
        for self.result_element in self.result_elements:
            self.result_for_elements.append(self._find_in_element())

        return self.result_for_elements


    def _find_in_element(self):
        """function search in element necessary information"""
        if self.selector_dict[self.entity]['parse'] == 'link':
            return self.result_element.links.pop()
        elif self.selector_dict[self.entity]['parse'] == 'text':
            return self.result_element.text


class Parser(BaseParser):
    """
    Updated parser object with headers/proxies
    """
    def __init__(self, use_proxy=True, use_headers=True):
        super().__init__()

        if use_proxy:
            self.proxies = PROXY_TUPLE
        else:
            self.proxies = None

        if use_headers:
            self.headers = HEADERS_TUPLE
        else:
            self.headers = None

    def _get_request(self):
        """
        Method for get request, handle a 404 response, connection error - change proxy and headers no more than 10 times
        """
        self.connection_count = 1
        while self.connection_count < 10:
            try:
                self.current_headers = choice(self.headers)
                self.current_proxy = choice(self.proxies)
                self.response = self.session.get(self.current_url, headers=self.current_headers, proxies=self.current_proxy)
                if self.response.status_code == 404:
                    return "Page not found"
                else:
                    return self.response.html
            except ConnectionError:
                self.connection_count += 1
                continue

        return "Connection failed"

    def ajax_parser(self, url, search_tuple):
        """

        """
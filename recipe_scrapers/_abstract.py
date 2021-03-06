import requests
from bs4 import BeautifulSoup

from ._exception_handling import ExceptionHandlingMetaclass
from ._schemaorg import SchemaOrg
from ._decorators import Decorators


# some sites close their content for 'bots', so user-agent must be supplied
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}


class AbstractScraper(metaclass=ExceptionHandlingMetaclass):

    def __init__(self, url, exception_handling=True, meta_http_equiv=False, test=False):
        if test:  # when testing, we load a file
            with url:
                page_data = url.read()
        else:
            page_data = requests.get(url, headers=HEADERS).content

        self.exception_handling = exception_handling
        self.meta_http_equiv = meta_http_equiv
        self.soup = BeautifulSoup(page_data, "html.parser")
        self.schema = SchemaOrg(page_data)
        self.url = url
        # if self.schema.data:
        #     print("Class: %s has schema." % (
        #         self.__class__.__name__
        #     ))

    def url(self):
        return self.url

    def host(self):
        """ get the host of the url, so we can use the correct scraper """
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    def title(self):
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    def total_time(self):
        """ total time it takes to preparate the recipe in minutes """
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    def yields(self):
        """ The number of servings or items in the recipe """
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    @Decorators.og_image_get
    def image(self):
        raise NotImplementedError("This should be implemented.")

    @Decorators.bcp47_validate
    @Decorators.schema_org_priority
    def language(self):
        """
        Human language the recipe is written in.

        May be overridden by individual scrapers.
        """
        candidate_languages = set()
        html = self.soup.find(
            'html',
            {'lang': True}
        )
        candidate_languages.add(html.get('lang'))

        # Deprecated: check for a meta http-equiv header
        # See: https://www.w3.org/International/questions/qa-http-and-lang
        meta_language = self.soup.find(
            'meta',
            {
                'http-equiv': lambda x: x and x.lower() == 'content-language',
                'content': True
            }
        ) if self.meta_http_equiv else None
        if meta_language:
            for language in meta_language.get('content').split(','):
                candidate_languages.add(language)
                break

        # If other langs exist, remove 'en' commonly generated by HTML editors
        if len(candidate_languages) > 1 and 'en' in candidate_languages:
            candidate_languages.remove('en')

        # Return the first candidate language
        for language in candidate_languages:
            return language

    @Decorators.schema_org_priority
    def ingredients(self):
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    def instructions(self):
        raise NotImplementedError("This should be implemented.")

    @Decorators.schema_org_priority
    def ratings(self):
        raise NotImplementedError("This should be implemented.")

    def reviews(self):
        raise NotImplementedError("This should be implemented.")

    def links(self):
        invalid_href = ('#', '')
        links_html = self.soup.findAll('a', href=True)

        return [
            link.attrs
            for link in links_html
            if link['href'] not in invalid_href
        ]

    def steps(self):
        """
        Text and Image of the instructions steps

        Try to fetch it from an hypothetical step structure
        based on cucchiaio.it
        :return array of steps made of texts and images
        """
        try:
            steps = []
            steps_container = self.soup.find('div', {'class': 'procedure-par'})
            for step_elem in steps_container.children:
                step = {"texts": [], "images": []}
                step_container = step_elem.find()
                texts = step_container.findAll(
                    'div',
                    {'class': 'step', 'content': True}
                )
                step["texts"] = texts
                images = step_container.findAll(
                    'div',
                    {'class': 'og:image', 'content': True}
                )
                step["images"] = images
                steps.append(step)
            return steps
        except AttributeError:  # if image not found
            raise NotImplementedError("This should be implemented.")

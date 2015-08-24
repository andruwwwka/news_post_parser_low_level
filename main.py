import re
import os
import sys
# from grab.spider import Spider, Task
import lxml.html as html

default_selectors_config = {
    'default': {
        'title': '//title',
        'text': '//div//p',
        'link_text': '/a',
        'link': '/@href',
    }
}

cur_dir = os.path.abspath(os.curdir)


class RegexValidator(object):
    _pattern = ''

    def __init__(self, pattern=''):
        self.pattern = pattern
        self._regex = re.compile(self.pattern, re.IGNORECASE)

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, new_patern):
        if self.pattern != new_patern:
            self._pattern = new_patern
            self._regex = re.compile(self.pattern, re.IGNORECASE)


class UrlValidator(RegexValidator):
    url_pattern = r'^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|' \
                  r'[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$'

    def __init__(self, pattern=''):
        super(UrlValidator, self).__init__(
            pattern or self.url_pattern
        )

    def is_valid(self, url=''):
        return bool(re.match(self._regex, url))


class FileWriter(object):

    def __init__(self, url):
        self.url = url
        filedir = '{}/{}'.format(cur_dir, self.url[self.url.index('://')+3:])
        if filedir[-1] == '/':
            filedir = filedir[:-1]
        file_path = filedir[:filedir.rindex('/')]
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = '{}.txt'.format(filedir.split('/')[-1].split('.')[0])
        self.result_path = '{}/{}'.format(file_path, file_name)
        self.was_writen = os.path.exists(self.result_path)
        if not self.was_writen:
            self.file = open(self.result_path, 'w')

    def write(self, value):
        self.file.write('{}{}'.format(value, '\n'))

    def destroy(self):
        if self.was_writen:
            print('Url already {} was parsed to file {}'.format(self.url, self.result_path))
            return
        self.file.close()
        print('Url {} was parsed to file {}'.format(self.url, self.result_path))


class FormatTextBlock(object):
    max_items_in_string = 80

    def __init__(self, block):
        self.block = block

    def format(self):
        words = self.block.split()
        result = ''
        line = ''
        for word in words:
            if len(line) + len(word) < self.max_items_in_string:
                line += (' ' if line else '') + word
            else:
                if line:
                    result += '{}{}'.format('\n', line)
                line = word
        if line:
            result += '{}{}'.format('\n', line)
        return result


class SelectorValidator(object):

    def __init__(self, selector, url):
        self.selector = selector
        self.url = url

    def is_valid(self):
        if self.url in self.selector:
            for config in ['title', 'text', 'link_text', 'link']:
                if not config in self.selector[self.url] or not self.selector[self.url][config]:
                    return False
            return True
        return False


# class SimpleSpider(Spider):
#
#     def __init__(self, *args, **kwargs):
#         self.initial_urls = kwargs.pop('urls')
#         self.selectors_config = kwargs.pop('selectors_config')
#         self.url_validator = UrlValidator()
#         super(SimpleSpider, self).__init__(*args, **kwargs)
#
#     def start_task_generator(self):
#         """
#         Process `self.initial_urls` list and `self.task_generator`
#         method.  Generate first portion of tasks.
#         """
#         if self.initial_urls:
#             for url in self.initial_urls:
#                 if not self.url_validator.is_valid(url):
#                     print('Could not resolve relative URL because url [{}] is not valid.\n'.format(url))
#                     continue
#                 self.add_task(Task('initial', url=url))
#         self.task_generator_object = self.task_generator()
#         self.task_generator_enabled = True
#         # Initial call to task generator before spider has started working
#         self.process_task_generator()
#
#     def task_initial(self, grab, task):
#         yield Task('parse', grab=grab)
#
#     def task_parse(self, grab, task):
#         writer = FileWriter(task.url)
#         if not writer.was_writen:
#             site = task.url.split('/')[2]
#             validator = SelectorValidator(url=site, selector=self.selectors_config)
#             settings_template = self.selectors_config.get(site) if validator.is_valid() \
#                 else default_selectors_config.get('default')
#             head_tag = settings_template.get('title')
#             for elem in grab.doc.select(head_tag):
#                 writer.write(elem._node.text_content())
#             xpath_param_text = settings_template.get('text')
#             xpath_param_link_text = '{}{}'.format(xpath_param_text, settings_template.get('link_text'))
#             xpath_param_link = '{}{}'.format(xpath_param_link_text, settings_template.get('link'))
#             for elem in grab.doc.select(xpath_param_text):
#                 url_name_list = elem.select(xpath_param_link_text).selector_list
#                 url_link_list = elem.select(xpath_param_link).selector_list
#                 maping_url = zip(url_name_list, url_link_list)
#                 article_element = elem._node.text_content()
#                 for name, link in maping_url:
#                     if name.text() in article_element:
#                         name_index = article_element.index(name.text()) + len(name.text())
#                         article_element = '{}[{}]{}'.format(article_element[:name_index], link.text(), article_element[name_index:])
#                 format_maker = FormatTextBlock(article_element)
#                 writer.write(format_maker.format())
#         writer.destroy()


class Parser(object):

    def __init__(self, urls, selectors_config):
        self.initial_urls = urls
        self.selectors_config = selectors_config
        self.url_validator = UrlValidator()

    def parse(self, url):
        writer = FileWriter(url)
        if not writer.was_writen:
            page = html.parse(url)
            # root = page.get_root()
            site = url.split('/')[2]
            validator = SelectorValidator(url=site, selector=self.selectors_config)
            settings_template = self.selectors_config.get(site) if validator.is_valid() \
                else default_selectors_config.get('default')
            head_tag = settings_template.get('title')
            for elem in page.xpath(head_tag):
                writer.write(elem.text_content())
            xpath_param_text = settings_template.get('text')
            xpath_param_link_text = '{}{}'.format(xpath_param_text, settings_template.get('link_text'))
            xpath_param_link = '{}{}'.format(xpath_param_link_text, settings_template.get('link'))
            for elem in page.xpath(xpath_param_text):
                url_name_list = elem.xpath(xpath_param_link_text)
                url_link_list = elem.xpath(xpath_param_link)
                maping_url = zip(url_name_list, url_link_list)
                article_element = elem.text_content()
                for name, link in maping_url:
                    if name.text() in article_element:
                        name_index = article_element.index(name.text()) + len(name.text())
                        article_element = '{}[{}]{}'.format(article_element[:name_index], link.text(), article_element[name_index:])
                format_maker = FormatTextBlock(article_element)
                writer.write(format_maker.format())
        writer.destroy()
        return True

    def run(self):
        for url in self.initial_urls:
            self.parse(url)
        return True


if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('Parser takes at least 1 argument (0 given)')
    urls = sys.argv[1:]
    settings_path = '{}/settings'.format(cur_dir)
    if os.path.exists(settings_path):
        settings_file = open(settings_path, 'r')
        selectors_config = eval(settings_file.read())
        settings_file.close()
    else:
        selectors_config = default_selectors_config
    bot = Parser(urls=urls, selectors_config=selectors_config)
    bot.run()

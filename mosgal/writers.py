import shutil
from typing import Iterable
import pathlib
from jinja2 import Environment, select_autoescape, FileSystemLoader

from mosgal.base_models import BaserWriter, Collection

env = Environment(
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class TemplateMixin:

    def __init__(self, template_name=''):
        self.template_name = template_name

    def render_template(self, **kwargs):
        template = env.get_template(self.template_name)
        return template.render(**kwargs)


class BuildDirectory(BaserWriter):

    def __init__(self, build: pathlib.Path, writers: Iterable[BaserWriter] = ()):
        super().__init__()

        self.writers = writers
        self.build = build

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs) -> None:
        # create build directory
        if self.build.exists():
            shutil.rmtree(self.build)

        self.build.mkdir()

        # apply writers in build directory
        for write in self.writers:
            write(collections, self.build)

        # move build directory into destination
        if destination.exists():
            shutil.rmtree(destination)

        self.build.rename(destination)


class WriteTemplate(TemplateMixin, BaserWriter):

    def __init__(self, template_name, destination_file: pathlib.Path()):
        super().__init__(template_name)
        self.destination_file = destination_file

    def get_context_data(self, collections: Iterable[Collection], *args, **kwargs):
        return {}

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs):
        with pathlib.Path.joinpath(destination, self.destination_file).open('w') as f:
            f.write(self.render_template(**self.get_context_data(collections, *args, **kwargs)))


class WriteIndex(WriteTemplate):
    def __init__(self):
        super().__init__('index.html', 'index.html')

    def get_context_data(self, collections: Iterable[Collection], *args, **kwargs):
        return {}
